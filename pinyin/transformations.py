#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

from logger import log
from pinyin import *
from utils import *


# Convenience wrapper around the TrimErhuaVisitor
def trimerhua(token):
    prefix, candidateer = token.accept(TrimErhuaVisitor())
    # NB: either thing may be None, but the TokenList filters them out
    return TokenList([prefix, candidateer])

class TrimErhuaVisitor(TokenVisitor):
    def visitText(self, text):
        return text, None

    def visitPinyin(self, pinyin):
        if pinyin.iser:
            return None, pinyin
        else:
            return pinyin, None

    def visitTonedCharacter(self, tonedcharacter):
        if tonedcharacter.iser:
            return None, tonedcharacter
        else:
            return tonedcharacter, None

    def visitWord(self, word):
        prefix, candidateer = word.token.accept(self)
        
        if prefix:
            # There was at least one non-er character, so return that only
            return Word(prefix), None
        else:
            # OK, the word contained only an er: return that as the new candidate
            return None, Word(candidateer)

    def visitTokenList(self, tokens):
        outputtokens, candidateer = TokenList(), None
        for token in tokens:
            outputtokens.append(candidateer) # NB: Nones are filtered by append
            output, candidateer = token.accept(self)
            outputtokens.append(output) # NB: Nones are filtered by append
        
        return outputtokens, candidateer


# Convenience wrapper around the ColorizerVisitor
def colorize(colorlist, token):
    value = token.accept(ColorizerVisitor(colorlist))
    return value

"""
Colorize readings according to the reading in the Pinyin.
* 2009 rewrites by Max Bolingbroke <batterseapower@hotmail.com>
* 2009 original version by Nick Cook <nick@n-line.co.uk> (http://www.n-line.co.uk)
"""
class ColorizerVisitor(MapTokenVisitor):
    def __init__(self, colorlist):
        self.colorlist = colorlist
        log.info("Using color list %s", self.colorlist)
        
    def visitText(self, text):
        return text

    def visitPinyin(self, pinyin):
        return self.colorize(pinyin)

    def visitTonedCharacter(self, tonedcharacter):
        return self.colorize(tonedcharacter)
    
    def colorize(self, token):
        return TokenList([
            Text(u'<span style="color:' + self.colorlist[token.tone - 1] + u'">'),
            token,
            Text(u'</span>')
          ])

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
def audioreadingforpack(mediapack, audioextensions, tokens):
    visitor = PinyinAudioReadingsVisitor(mediapack, audioextensions)
    tokens.accept(visitor)
    return (visitor.output, visitor.mediamissingcount)

class PinyinAudioReadingsVisitor(LeafTokenVisitor):
    def __init__(self, mediapack, audioextensions):
        self.mediapack = mediapack
        self.audioextensions = audioextensions
        
        self.output = []
        self.mediamissingcount = 0
    
    def visitText(self, text):
        pass

    def visitPinyin(self, pinyin):
        # Find possible base sounds we could accept
        possiblebases = [pinyin.numericformat(hideneutraltone=False)]
        if pinyin.tone == 5:
            # Sometimes we can replace tone 5 with 4 in order to deal with lack of '[xx]5.ogg's
            possiblebases.extend([pinyin.word, pinyin.word + '4'])
        elif u"u:" in pinyin.word:
            # Typically u: is written as v in filenames
            possiblebases.append(pinyin.word.replace(u"u:", u"v") + str(pinyin.tone))
    
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

    def visitWord(self, word):
        trimerhua(word.token).accept(self)

# Wrapper around the MaskHanziVisitor
def maskhanzi(expression, maskingcharacter, token):
    return token.accept(MaskHanziVisitor(expression, maskingcharacter))

class MaskHanziVisitor(MapTokenVisitor):
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
    
    class TrimErhuaTest(unittest.TestCase):
        def testTrimErhuaEmpty(self):
            self.assertEquals(flatten(trimerhua(TokenList([]))), u'')

        def testTrimErhuaSingleErPinyin(self):
            self.assertEquals(flatten(trimerhua(Pinyin(u'r5'))), u'r')
            self.assertEquals(flatten(trimerhua(TonedCharacter(u'儿', 5))), u'儿')
            self.assertEquals(flatten(trimerhua(Word(Pinyin(u'r5')))), u'r')
            self.assertEquals(flatten(trimerhua(Word(TonedCharacter(u'儿', 5)))), u'儿')
            self.assertEquals(flatten(trimerhua(TokenList([Pinyin(u'r5')]))), u'r')
            self.assertEquals(flatten(trimerhua(TokenList([TonedCharacter(u'儿', 5)]))), u'儿')

        def testTrimErhuaCharacters(self):
            self.assertEquals(flatten(trimerhua(Word(TokenList([TonedCharacter(u"一", 1), TonedCharacter(u"瓶", 2), TonedCharacter(u"儿", 5)])))), u"一瓶")

        def testTrimErhuaPinyin(self):
            self.assertEquals(flatten(trimerhua(Word(TokenList([Pinyin(u"yi1"), Pinyin(u"ping2"), Pinyin(u"r5")])))), u"yi1ping2")

        def testDontTrimErhuaOutsideWord(self):
            self.assertEquals(flatten(trimerhua(TokenList([Pinyin(u"yi1"), Pinyin(u"ping2"), Pinyin(u"r5")]))), u"yi1ping2r")

        def testDontTrimNonErhua(self):
            self.assertEquals(flatten(trimerhua(Word(TokenList([TonedCharacter(u"一", 1), TonedCharacter(u"瓶", 2)])))), u"一瓶")

    class MaskHanziTest(unittest.TestCase):
        def testMaskText(self):
            self.assertEquals(maskhanzi("ello", "mask", TokenList([Text("World"), Word(Text("Hello!")), Text(" "), Text("Jello")])),
                              TokenList([Text("World"), Word(Text("Hmask!")), Text(" "), Text("Jmask")]))
        
        def testMaskCharacter(self):
            self.assertEquals(maskhanzi("hen", "chicken", TokenList([Pinyin("hen3"), Word(TonedCharacter("hen", 3)), TonedCharacter("mhh", 2)])),
                              TokenList([Pinyin("hen3"), Word(Text("chicken")), TonedCharacter("mhh", 2)]))

    unittest.main()
