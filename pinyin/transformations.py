#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import re
import cStringIO

from logger import log
from pinyin import *
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
        wordcontours = (match.group(1) or "").split("~")[:-1] + [match.group(2)]
        maketwosifpoly = lambda what: len(what) == 1 and what or '2' * len(what)
        makeprefixtwos = lambda what: '2' * (len(what) - 1) + '3'
        return "~".join([maketwosifpoly(wordcontour) for wordcontour in wordcontours[:-1]] + [makeprefixtwos(wordcontours[-1])])
    tonecontour = re.sub(r"((?:3+)\~+)*(3+)", dealWithThrees, tonecontour)
    
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
    return [word.concatmap(ColorizerVisitor(colorlist)) for word in words]

class ColorizerVisitor(TokenVisitor):
    def __init__(self, colorlist):
        self.colorlist = colorlist
        log.info("Using color list %s", self.colorlist)
        
    def visitText(self, text):
        return [text]

    def visitPinyin(self, pinyin):
        return self.colorize(pinyin)

    def visitTonedCharacter(self, tonedcharacter):
        return self.colorize(tonedcharacter)
    
    def colorize(self, token):
        # Colors should always be based on the written tone, but they will be
        # made lighter if a sandhi applies
        color = self.colorlist[token.toneinfo.written - 1]
        if token.toneinfo.spoken != token.toneinfo.written:
            color = sandhifycolor(color)
        
        return [
            Text(u'<span style="color:' + color + u'">'),
            token,
            Text(u'</span>')
          ]

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
        if pinyin.toneinfo.spoken == 5:
            # Sometimes we can replace tone 5 with 4 in order to deal with lack of '[xx]5.ogg's
            possiblebases.extend([pinyin.word, pinyin.word + '4'])
        elif u"u:" in pinyin.word:
            # Typically u: is written as v in filenames
            possiblebases.append(pinyin.word.replace(u"u:", u"v") + str(pinyin.toneinfo.spoken))
    
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
            log.warning("Couldn't find media for %s in %s", pinyin, self.mediapack)
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
        return Text(text.replace(self.expression, self.maskingcharacter))

    def visitPinyin(self, pinyin):
        return pinyin

    def visitTonedCharacter(self, tonedcharacter):
        if unicode(tonedcharacter) == self.expression:
            return Text(self.maskingcharacter)
        else:
            return tonedcharacter

# Testsuite
if __name__=='__main__':
    import unittest
    import dictionary
    
    from media import MediaPack
    
    # Shared dictionary
    englishdict = Thunk(lambda: dictionary.PinyinDictionary.load("en"))
    
    # Default tone color list for tests
    colorlist = [
        u"#ff0000",
        u"#ffaa00",
        u"#00aa00",
        u"#0000ff",
        u"#545454"
      ]
    
    class PinyinColorizerTest(unittest.TestCase):
        def testRSuffix(self):
            self.assertEqual(self.colorize(u"哪兒"), '<span style="color:#00aa00">na3</span><span style="color:#545454">r</span>')
        
        def testColorize(self):
            self.assertEqual(self.colorize(u"妈麻马骂吗"),
                '<span style="color:#ff0000">ma1</span> <span style="color:#ffaa00">ma2</span> ' +
                '<span style="color:#00aa00">ma3</span> <span style="color:#0000ff">ma4</span> ' +
                '<span style="color:#545454">ma</span>')
    
        def testMixedEnglishChinese(self):
            self.assertEqual(self.colorize(u'Small 小 - Horse'),
                'Small <span style="color:#00aa00">xiao3</span> - Horse')
        
        def testPunctuation(self):
            self.assertEqual(self.colorize(u'小小!'),
                '<span style="color:#00aa00">xiao3</span> <span style="color:#00aa00">xiao3</span>!')
    
        def testUseSpokenToneRatherThanWrittenOne(self):
            self.assertEqual(flatten(colorize(colorlist, [Word(Pinyin("xiao", ToneInfo(written=3, spoken=2)))])),
                '<span style="color:#66cc66">xiao3</span>')
    
        # Test helpers
        def colorize(self, what):
            return flatten(colorize(colorlist, englishdict.reading(what)))
    
    class CharacterColorizerTest(unittest.TestCase):
        def testColorize(self):
            self.assertEqual(self.colorize(u"妈麻马骂吗"),
                u'<span style="color:#ff0000">妈</span><span style="color:#ffaa00">麻</span>' +
                u'<span style="color:#00aa00">马</span><span style="color:#0000ff">骂</span>' +
                u'<span style="color:#545454">吗</span>')
    
        def testMixedEnglishChinese(self):
            self.assertEqual(self.colorize(u'Small 小 - Horse'),
                u'Small <span style="color:#00aa00">小</span> - Horse')
        
        def testPunctuation(self):
            self.assertEqual(self.colorize(u'小小!'),
                u'<span style="color:#00aa00">小</span><span style="color:#00aa00">小</span>!')
    
        def testUseSpokenToneRatherThanWrittenOne(self):
            self.assertEqual(flatten(colorize(colorlist, [Word(TonedCharacter(u"小", ToneInfo(written=3, spoken=2)))])),
                u'<span style="color:#66cc66">小</span>')
    
        # Test helpers
        def colorize(self, what):
            return flatten(colorize(colorlist, englishdict.tonedchars(what)))
    
    class PinyinAudioReadingsTest(unittest.TestCase):
        default_raw_available_media = ["na3.mp3", "ma4.mp3", "xiao3.mp3", "ma3.mp3", "ci2.mp3", "dian3.mp3",
                                       "a4.mp3", "nin2.mp3", "ni3.ogg", "hao3.ogg", "gen1.ogg", "gen1.mp3"]
        
        def testRSuffix(self):
            self.assertHasReading(u"哪兒", ["na3.mp3"])
            self.assertHasReading(u"哪儿", ["na3.mp3"])
        
        def testFifthTone(self):
            self.assertHasReading(u"的", ["de5.mp3"], raw_available_media=["de5.mp3", "de.mp3", "de4.mp3"])
            self.assertHasReading(u"了", ["le.mp3"], raw_available_media=["le4.mp3", "le.mp3"])
            self.assertHasReading(u"吗", ["ma4.mp3"], raw_available_media=["ma4.mp3"])
        
        def testNv(self):
            self.assertHasReading(u"女", ["nu:3.mp3"], raw_available_media=["nv3.mp3", "nu:3.mp3", "nu3.mp3"])
            self.assertHasReading(u"女", ["nv3.mp3"], raw_available_media=["nu3.mp3", "nv3.mp3"])
            self.assertMediaMissing(u"女", raw_available_media=["nu3.mp3"])
            
        def testLv(self):
            self.assertHasReading(u"侣", ["lv3.mp3"], raw_available_media=["lv3.mp3"])
            self.assertMediaMissing(u"侣", raw_available_media=["lu3.mp3"])
            self.assertHasReading(u"掠", ["lve4.mp3"], raw_available_media=["lve4.mp3"])
            self.assertMediaMissing(u"掠", raw_available_media=["lue4.mp3"])
        
        def testJunkSkipping(self):
            # NB: NOT a partial reading, because none of the tokens here are Pinyin it doesn't know about
            self.assertHasReading(u"Washington ! ! !", [])
        
        def testMultipleCharacters(self):
            self.assertHasReading(u"小马词典", ["xiao3.mp3", "ma3.mp3", "ci2.mp3","dian3.mp3"])
        
        def testMixedEnglishChinese(self):
            self.assertHasReading(u"啊 The Small 马 Dictionary", ["a4.mp3", "ma3.mp3"])
        
        def testPunctuation(self):
            self.assertHasReading(u"您 (pr.)", ["nin2.mp3"])
        
        def testSecondaryExtension(self):
            self.assertHasReading(u"你好", ["ni3.ogg", "hao3.ogg"])
    
        def testMixedExtensions(self):
            self.assertHasReading(u"你马", ["ni3.ogg", "ma3.mp3"])
    
        def testPriority(self):
            self.assertHasReading(u"根", ["gen1.mp3"])
    
        def testMediaMissing(self):
            self.assertMediaMissing(u"根", raw_available_media=[".mp3"])
    
        def testCaptializationInPinyin(self):
            # NB: 上海 is in the dictionary with capitalized pinyin (Shang4 hai3)
            self.assertHasReading(u"上海", ["shang4.mp3", "hai3.mp3"], raw_available_media=["shang4.mp3", "hai3.mp3"])
        
        def testCapitializationInFilesystem(self):
            self.assertHasReading(u"根", ["GeN1.mP3"], available_media={"GeN1.mP3" : "GeN1.mP3" })
    
        def testDontMixPacks(self):
            packs = [MediaPack("Foo", {"ni3.mp3" : "ni3.mp3", "ma3.mp3" : "ma3.mp3"}), MediaPack("Bar", {"hao3.mp3" : "hao3.mp3"})]
            self.assertHasPartialReading(u"你好马", ["ni3.mp3", "ma3.mp3"], bestpackshouldbe=packs[0], mediapacks=packs)
    
        def testUseBestPack(self):
            packs = [MediaPack("Foo", {"xiao3.mp3" : "xiao3.mp3", "ma3.mp3" : "ma3.mp3"}),
                     MediaPack("Bar", {"ma3.mp3" : "ma3.mp3", "ci2.mp3" : "ci2.mp3", "dian3.mp3" : "dian3.mp3"})]
            self.assertHasPartialReading(u"小马词典", ["ma3.mp3", "ci2.mp3", "dian3.mp3"], bestpackshouldbe=packs[1], mediapacks=packs)
    
        def testRandomizeBestPackOnTie(self):
            pack1 = MediaPack("Foo", {"ni3.mp3" : "PACK1.mp3"})
            pack2 = MediaPack("Bar", {"ni3.mp3" : "PACK2.mp3"})
    
            gotpacks = []
            for n in range(1, 10):
                gotpack, _, _ = PinyinAudioReadings([pack1, pack2], [".mp3", ".ogg"]).audioreading(englishdict.reading(u"你"))
                gotpacks.append(gotpack)
            
            # This test will nondeterministically fail (1/2)^10 = 0.01% of the time
            self.assertTrue(pack1 in gotpacks)
            self.assertTrue(pack2 in gotpacks)
    
        def testUseSpokenToneRatherThanWrittenOne(self):
            mediapacks = [MediaPack("Foo", { "ma2.mp3" : "ma2.mp3", "ma3.mp3" : "ma3.mp3" })]
            mediapack, output, mediamissing = PinyinAudioReadings(mediapacks, [".mp3"]).audioreading([Word(Pinyin("ma", ToneInfo(written=2, spoken=3)))])
            self.assertEquals(mediapack, mediapacks[0])
            self.assertFalse(mediamissing)
            self.assertEquals(output, ["ma3.mp3"])
    
        # Test helpers
        def assertHasReading(self, what, shouldbe, **kwargs):
            bestpackshouldbe, mediapack, output, mediamissing = self.audioreading(what, **kwargs)
            self.assertEquals(bestpackshouldbe, mediapack)
            self.assertEquals(output, shouldbe)
            self.assertFalse(mediamissing)
        
        def assertHasPartialReading(self, what, shouldbe, **kwargs):
            bestpackshouldbe, mediapack, output, mediamissing = self.audioreading(what, **kwargs)
            self.assertEquals(bestpackshouldbe, mediapack)
            self.assertEquals(output, shouldbe)
            self.assertTrue(mediamissing)
            
        def assertMediaMissing(self, what, **kwargs):
            bestpackshouldbe, mediapack, output, mediamissing = self.audioreading(what, **kwargs)
            self.assertTrue(mediamissing)
        
        def audioreading(self, what, **kwargs):
            bestpackshouldbe, mediapacks = self.expandmediapacks(**kwargs)
            mediapack, output, mediamissing = PinyinAudioReadings(mediapacks, [".mp3", ".ogg"]).audioreading(englishdict.reading(what))
            return bestpackshouldbe, mediapack, output, mediamissing
        
        def expandmediapacks(self, mediapacks=None, available_media=None, raw_available_media=default_raw_available_media, bestpackshouldbe=None):
            if mediapacks:
                return bestpackshouldbe, mediapacks
            elif available_media:
                pack = MediaPack("Test", available_media)
                return pack, [pack]
            else:
                pack = MediaPack("Test", dict([(filename, filename) for filename in raw_available_media]))
                return pack, [pack]
    
    class ToneSandhiTest(unittest.TestCase):
        def testDoesntAffectWrittenTones(self):
            self.assertEquals(flatten(tonesandhi([Word(Pinyin.parse("hen3")), Word(Pinyin.parse("hao3"))])), "hen3hao3")
        
        def testText(self):
            self.assertSandhi(Word(Text("howdy")), "howdy")
        
        def testSingleThirdTone(self):
            self.assertSandhi(Word(Pinyin.parse("hen3")), "hen3")
        
        def testSimple(self):
            self.assertSandhi(Word(Pinyin.parse("hen3")), Word(Pinyin.parse("hao3")), "hen2hao3")
            self.assertSandhi(Word(Pinyin.parse("hen3"), Pinyin.parse("hao3")), "hen2hao3")
        
        def testIgnoresWhitespace(self):
            self.assertSandhi(Word(Pinyin.parse("hen3")), Word(Text(" ")), Word(Pinyin.parse("hao3")), "hen2 hao3")
            self.assertSandhi(Word(Pinyin.parse("hen3"), Text(" "), Pinyin.parse("hao3")), "hen2 hao3")
        
        def testMultiMono(self):
            self.assertSandhi(Word(Pinyin.parse("bao3"), Pinyin.parse("guan3")), Word(Pinyin.parse("hao3")), "bao2guan2hao3")
        
        def testMonoMulti(self):
            self.assertSandhi(Word(Pinyin.parse("lao3")), Word(Pinyin.parse("bao3"), Pinyin.parse("guan3")), "lao3bao2guan3")
        
        # def testYiFollowedByFour(self):
        #     self.assertSandhi(Word(Pinyin.parse("yi1")), Word(Pinyin.parse("ding4")), "yi2ding4")
        # 
        # def testYiFollowedByOther(self):
        #     self.assertSandhi(Word(Pinyin.parse("yi1")), Word(Pinyin.parse("tian1")), "yi4tian1")
        #     self.assertSandhi(Word(Pinyin.parse("yi1")), Word(Pinyin.parse("nian2")), "yi4nian2")
        #     self.assertSandhi(Word(Pinyin.parse("yi1")), Word(Pinyin.parse("qi3")), "yi4qi3")
        # 
        # def testYiBetweenTwoWords(self):
        #     self.assertSandhi(Word(Pinyin.parse("kan4")), Word(Pinyin.parse("yi1")), Word(Pinyin.parse("kan4")), "kan4yikan4")
        # 
        # # NB: don't bother to implement yi1 sandhi that depends on context such as whether we are
        # # counting sequentially or using yi1 as an ordinal number
        # 
        # def testBuFollowedByFourth(self):
        #     self.assertSandhi(Word(Pinyin.parse("bu4")), Word(Pinyin.parse("shi4")), "bu2shi4")
        # 
        # def testBuBetweenTwoWords(self):
        #     self.assertSandhi(Word(Pinyin.parse("shi4")), Word(Pinyin.parse("bu4")), Word(Pinyin.parse("shi4")), "shi4bushi4")
        
        # Test helpers
        def assertSandhi(self, *args):
            self.assertEquals(flatten(self.copySpokenToWritten(tonesandhi(args[:-1]))), args[-1])
        
        def copySpokenToWritten(self, words):
            class CopySpokenToWrittenVisitor(TokenVisitor):
                def visitText(self, text):
                    return text
                
                def visitPinyin(self, pinyin):
                    return Pinyin(pinyin.word, ToneInfo(written=pinyin.toneinfo.spoken))
                
                def visitTonedCharacter(self, tonedcharacter):
                    return TonedCharacter(unicode(tonedcharacter), ToneInfo(written=tonedcharacter.toneinfo.spoken))
            
            return [word.map(CopySpokenToWrittenVisitor()) for word in words]
    
    class TrimErhuaTest(unittest.TestCase):
        def testTrimErhuaEmpty(self):
            self.assertEquals(flatten(trimerhua([])), u'')

        def testTrimErhuaCharacters(self):
            self.assertEquals(flatten(trimerhua([Word(TonedCharacter(u"一", 1), TonedCharacter(u"瓶", 2), TonedCharacter(u"儿", 5))])), u"一瓶")

        def testTrimErhuaPinyin(self):
            self.assertEquals(flatten(trimerhua([Word(Pinyin.parse(u"yi1"), Pinyin.parse(u"ping2"), Pinyin.parse(u"r5"))])), u"yi1ping2")
            self.assertEquals(flatten(trimerhua([Word(Pinyin.parse(u"yi1")), Word(Pinyin.parse(u"ping2"), Pinyin.parse(u"r5"))])), u"yi1ping2")

        def testDontTrimNonErhua(self):
            self.assertEquals(flatten(trimerhua([Word(TonedCharacter(u"一", 1), TonedCharacter(u"瓶", 2))])), u"一瓶")

        def testTrimSingleErHua(self):
            self.assertEquals(flatten(trimerhua([Word(Pinyin.parse(u'r5'))])), u'')
            self.assertEquals(flatten(trimerhua([Word(TonedCharacter(u'儿', 5))])), u'')
            self.assertEquals(flatten(trimerhua([Word(Pinyin.parse(u'r5'))])), u'')
            self.assertEquals(flatten(trimerhua([Word(TonedCharacter(u'儿', 5))])), u'')
            self.assertEquals(flatten(trimerhua([Word(Pinyin.parse(u'r5'))])), u'')
            self.assertEquals(flatten(trimerhua([Word(TonedCharacter(u'儿', 5))])), u'')

    class MaskHanziTest(unittest.TestCase):
        def testMaskText(self):
            self.assertEquals(maskhanzi("ello", "mask", [Word(Text("World")), Word(Text("Hello!")), Word(Text(" "), Text("Jello"))]),
                              [Word(Text("World")), Word(Text("Hmask!")), Word(Text(" "), Text("Jmask"))])
        
        def testMaskCharacter(self):
            self.assertEquals(maskhanzi("hen", "chicken", [Word(Pinyin.parse("hen3")), Word(TonedCharacter("hen", 3)), Word(TonedCharacter("mhh", 2))]),
                              [Word(Pinyin.parse("hen3")), Word(Text("chicken")), Word(TonedCharacter("mhh", 2))])

    unittest.main()
