#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import cStringIO
import random
import re

from logger import log
from model import *
from utils import *


# TODO: apply tone sandhi at the dictionary stage, to save having to do it in 3 places in the updater?
# Only thing to worry about is loss of accuracy due to the decreased amount of context...

"""
Apply tone sandhi rules to rewrite the tones in the given string. For the rules
see: <http://en.wikipedia.org/wiki/Standard_Mandarin#Tone_sandhi>

NB: we don't implement this very well yet. Give it time..
"""
def tonesandhi(words):
    # 1) Gather the tone contour into a string
    tonecontourio = cStringIO.StringIO()
    gathervisitor = GatherToneContourVisitor(tonecontourio)
    for word in words:
        word.accept(gathervisitor)
        tonecontourio.write("~")
    tonecontour = tonecontourio.getvalue()
    tonecontourio.close()
    
    
    # 2) Rewrite it (ewww!)
    
    log.info("Rewriting tone sandhi for contour %s", tonecontour)
    
    # NB: must match strings of ~ in the following in order to ignore words
    # which consist entirely of blank space. Tian'a, this is unbelievably horrible!
    
    # Top priority:
    #  33~3 -> 22~3
    #  3~33 -> 3~23
    # (and the more general sandhi effect with strings of length > 3)
    def dealWithThrees(match):
        # a) Split the match into a list of strings of 3 per word
        wordcontours = (match.group(1) or "").split("~")[:-1] + [match.group(2)]
        
        # b) Build the result
        #   i) For everything but the last word, turn the tone into 2 if it is monosyllabic
        maketwosifpoly = lambda what: len(what) == 1 and what or '2' * len(what)
        #   ii) For the last word, always end with a sequence of 2s followed by a 3
        makeprefixtwos = lambda what: '2' * (len(what) - 1) + '3'
        replacement = "~".join([maketwosifpoly(wordcontour) for wordcontour in wordcontours[:-1]] + [makeprefixtwos(wordcontours[-1])])
        
        log.debug("Rewrote complex tone sandhi %s into %s", match.group(0), replacement)
        return replacement
    tonecontour = re.sub(r"((?:3+\~+)*)(3+)", dealWithThrees, tonecontour)
    
    # Low priority (let others take effect first):
    #  33  -> 23 (though this is already caught by the code above, actually)
    #  3~3 -> 2~3
    tonecontour = re.sub(r"3(\~*)3", r"2\g<1>3", tonecontour)
    
    log.info("Final contour computed as %s", tonecontour)
    
    # 3) Apply the new contour to the words
    finalwords = []
    tonecontourqueue = list(tonecontour[::-1])
    applyvisitor = ApplyToneContourVisitor(tonecontourqueue)
    for word in words:
        finalwords.append(word.map(applyvisitor))
        assert tonecontourqueue.pop() == "~"
    return finalwords

class GatherToneContourVisitor(TokenVisitor):
    def __init__(self, tonecontourio):
        self.tonecontourio = tonecontourio

    def visitText(self, text):
        if len(text.strip()) != 0:
            self.tonecontourio.write("_")

    def visitPinyin(self, pinyin):
        self.tonecontourio.write(str(pinyin.toneinfo.written))
        
    def visitTonedCharacter(self, tonedcharacter):
        self.tonecontourio.write(str(tonedcharacter.toneinfo.written))

class ApplyToneContourVisitor(TokenVisitor):
    def __init__(self, tonecontourqueue):
        self.tonecontourqueue = tonecontourqueue
    
    def visitText(self, text):
        if len(text.strip()) != 0:
            assert self.tonecontourqueue.pop() in "_"
        return text

    def visitPinyin(self, pinyin):
        return Pinyin(pinyin.word, ToneInfo(written=pinyin.toneinfo.written, spoken=int(self.tonecontourqueue.pop())))
    
    def visitTonedCharacter(self, tonedcharacter):
        return TonedCharacter(unicode(tonedcharacter), ToneInfo(written=tonedcharacter.toneinfo.written, spoken=int(self.tonecontourqueue.pop())))

"""
Remove all r5 characters from the supplied words.
"""
def trimerhua(words):
    return [word.concatmap(TrimErhuaVisitor()) for word in words]

class TrimErhuaVisitor(TokenVisitor):
    def visitText(self, text):
        return [text]

    def visitPinyin(self, pinyin):
        if pinyin.iser:
            return []
        else:
            return [pinyin]

    def visitTonedCharacter(self, tonedcharacter):
        if tonedcharacter.iser:
            return []
        else:
            return [tonedcharacter]


"""
Colorize readings according to the reading in the Pinyin.
* 2009 rewrites by Max Bolingbroke <batterseapower@hotmail.com>
* 2009 original version by Nick Cook <nick@n-line.co.uk> (http://www.n-line.co.uk)
"""
def colorize(colorlist, words):
    return [word.map(ColorizerVisitor(colorlist)) for word in words]

class ColorizerVisitor(TokenVisitor):
    def __init__(self, colorlist):
        self.colorlist = colorlist
        log.info("Using color list %s", self.colorlist)
        
    def visitText(self, text):
        return text

    def visitPinyin(self, pinyin):
        return self.colorize(pinyin, lambda htmlattrs: Pinyin(pinyin.word, pinyin.toneinfo, htmlattrs))

    def visitTonedCharacter(self, tonedcharacter):
        return self.colorize(tonedcharacter, lambda htmlattrs: TonedCharacter(unicode(tonedcharacter), tonedcharacter.toneinfo, htmlattrs))
    
    def colorize(self, token, rebuild):
        # Colors should always be based on the written tone, but they will be
        # made lighter if a sandhi applies
        color = self.colorlist[token.toneinfo.written - 1]
        if token.toneinfo.spoken != token.toneinfo.written:
            color = sandhifycolor(color)
        
        # Make sure we don't overwrite any colors that the user set up.
        # Perhaps this is suboptimal, but it is the only sane thing to do -
        # in particular since it means we don't screw up sandhi coloring
        # when coloring a "Reading" field which was set up by the PyTK.
        if "color" not in token.htmlattrs:
            htmlattrs = token.htmlattrs.copy()
            htmlattrs["color"] = color
            return rebuild(htmlattrs)
        else:
            return token

def sandhifycolor(color):
    # Lighten up the color by halving saturation and increasing value
    # by 20%. This was chosen to match Nicks choice of how to change green
    # (tone 3) when sandhi applies: he wanted to go:
    #  from 00AA00 = (120, 100, 67)
    #  to   66CC66 = (120, 50,  80)
    r, g, b = parseHtmlColor(color)
    h, s, v = rgbToHSV(r, g, b)
    r, g, b = hsvToRGB(h, s * 0.5, min(v * 1.2, 1.0))
    finalcolor = toHtmlColor(r, g, b)
    
    log.info("Sandhified %s to %s", color, finalcolor)
    return finalcolor

"""
Output audio reading corresponding to a textual reading.
* 2009 rewrites by Max Bolingbroke <batterseapower@hotmail.com>
* 2009 original version by Nick Cook <nick@n-line.co.uk> (http://www.n-line.co.uk)
"""
class PinyinAudioReadings(object):
    def __init__(self, mediapacks, audioextensions):
        self.mediapacks = mediapacks
        self.audioextensions = audioextensions
    
    def audioreading(self, tokens):
        log.info("Requested audio reading for %d tokens", len(tokens))
        
        # Try possible packs to format the tokens. Basically, we
        # don't want to use a mix of sounds from different packs
        bestmediapacksoutputs, bestmediamissingcount = [], len(tokens) + 1
        for mediapack in self.mediapacks:
            log.info("Checking for reading in pack %s", mediapack.name)
            output, mediamissingcount = audioreadingforpack(mediapack, self.audioextensions, trimerhua(tokens))
            
            # We will end up choosing one of the packs that minimizes the number of errors:
            if mediamissingcount == bestmediamissingcount:
                # Just as good as a previous pack, so this is an alternative
                bestmediapacksoutputs.append((mediapack, output))
            elif mediamissingcount < bestmediamissingcount:
                # Strictly better than the previous ones, so this is the new best option
                bestmediapacksoutputs = [(mediapack, output)]
                bestmediamissingcount = mediamissingcount
        
        # Did we get any result at all?
        if len(bestmediapacksoutputs) != 0:
            bestmediapack, bestoutput = random.choice(bestmediapacksoutputs)
            return bestmediapack, bestoutput, (bestmediamissingcount != 0)
        else:
            return None, [], True

# Simple wrapper around the PinyinAudioReadingsVisitor
def audioreadingforpack(mediapack, audioextensions, words):
    visitor = PinyinAudioReadingsVisitor(mediapack, audioextensions)
    [word.accept(visitor) for word in trimerhua(words)]
    return (visitor.output, visitor.mediamissingcount)

class PinyinAudioReadingsVisitor(TokenVisitor):
    def __init__(self, mediapack, audioextensions):
        self.mediapack = mediapack
        self.audioextensions = audioextensions
        
        self.output = []
        self.mediamissingcount = 0
    
    def visitText(self, text):
        pass

    def visitPinyin(self, pinyin):
        # Find possible base sounds we could accept
        possiblebases = [pinyin.numericformat(hideneutraltone=False, tone="spoken")]
        substitutions = waysToSubstituteAwayUUmlaut(pinyin.word)
        if pinyin.toneinfo.spoken == 5:
            # Sometimes we can replace tone 5 with 4 in order to deal with lack of '[xx]5.ogg's
            possiblebases.extend([pinyin.word, pinyin.word + '4'])
        elif substitutions is not None:
            # Typically u: is written as v in filenames
            possiblebases.extend([substitution + str(pinyin.toneinfo.spoken) for substitution in substitutions])
    
        # Find path to first suitable media in the possibilty list
        for possiblebase in possiblebases:
            media = self.mediapack.mediafor(possiblebase, self.audioextensions)
            if media:
                break
    
        if media:
            # If we've managed to find some media, we can put it into the output:
            self.output.append(media)
        else:
            # Otherwise, increment the count of missing media we use to determine optimality
            log.warning("Couldn't find media for %s (%s) in %s", pinyin, pinyin.numericformat(tone="spoken"), self.mediapack)
            self.mediamissingcount += 1

    def visitTonedCharacter(self, tonedcharacter):
        pass

"""
Replace occurences of the expression in the words with the masking character.
"""
def maskhanzi(expression, maskingcharacter, words):
    return [word.map(MaskHanziVisitor(expression, maskingcharacter)) for word in words]

class MaskHanziVisitor(TokenVisitor):
    def __init__(self, expression, maskingcharacter):
        self.expression = expression
        self.maskingcharacter = maskingcharacter
    
    def visitText(self, text):
        for substring in substrings(self.expression):
            if all([isHanzi(c) for c in substring]):
                text = text.replace(substring, self.maskingcharacter)

        return Text(text)

    def visitPinyin(self, pinyin):
        return pinyin

    def visitTonedCharacter(self, tonedcharacter):
        if unicode(tonedcharacter) in self.expression:
            return Text(self.maskingcharacter)
        else:
            return tonedcharacter
