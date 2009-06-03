#!/usr/bin/env python
# -*- coding: utf-8 -*-

from logger import log
from pinyin import *
from utils import *

"""
Colorize readings according to the reading in the Pinyin.
* 2009 rewrites by Max Bolingbroke <batterseapower@hotmail.com>
* 2009 original version by Nick Cook <nick@n-line.co.uk> (http://www.n-line.co.uk)
"""

class Colorizer(object):
    def __init__(self, colorlist):
        self.colorlist = colorlist
        log.info("Using color list %s", self.colorlist)
        
    def colorize(self, tokens):
        log.info("Requested colorization for %d tokens", len(tokens))
        
        output = TokenList()
        for token in tokens:
            if hasattr(token, "tone"):
                output.append(u'<span style="color:' + self.colorlist.get(token.tone) + u'">')
                output.append(token)
                output.append(u'</span>')
            else:
                output.append(token)
        
        return output

"""
Output audio reading corresponding to a textual reading.
* 2009 rewrites by Max Bolingbroke <batterseapower@hotmail.com>
* 2009 original version by Nick Cook <nick@n-line.co.uk> (http://www.n-line.co.uk)
"""
class PinyinAudioReadings(object):
    def __init__(self, mediapacks, audioextensions):
        self.mediapacks = mediapacks
        self.audioextensions = audioextensions
    
    def audioreadingforpack(self, mediapack, tokens):
        output = u""
        mediamissingcount = 0
        for token in tokens:
            # Remove any erhuas from audio before being generated.
            # For example we want 儿子 to be "er2 zi5" but "门儿" (men2r) must become "men2"
            # It seems unlikely we will ever get erhua audio (i.e "men2r.ogg") so this is likely to be permanent
            # DEBUG - add code fulfilling the above
            # Also skip anything that doesn't look like pinyin, such as English words
            if type(token) != Pinyin or token.numericformat(hideneutraltone=False) == "r5":
                continue
        
            # Find possible base sounds we could accept
            possiblebases = [token.numericformat(hideneutraltone=False)]
            if token.tone == 5:
                # Sometimes we can replace tone 5 with 4 in order to deal with lack of '[xx]5.ogg's
                possiblebases.extend([token.word, token.word + '4'])
            elif u"u:" in token.word:
                # Typically u: is written as v in filenames
                possiblebases.append(token.word.replace(u"u:", u"v") + str(token.tone))
        
            # Find path to first suitable media in the possibilty list
            for possiblebase in possiblebases:
                media = mediapack.mediafor(possiblebase, self.audioextensions)
                if media:
                    break
        
            if media:
                # If we've managed to find some media, we can put it into the output:
                output += '[sound:' + media +']'
            else:
                # Otherwise, increment the count of missing media we use to determine optimality
                log.warning("Couldn't find media for %s in %s", token, mediapack)
                mediamissingcount += 1
    
        return (output, mediamissingcount)
    
    def audioreading(self, tokens):
        log.info("Requested audio reading for %d tokens", len(tokens))
        
        # Try possible packs to format the tokens. Basically, we
        # don't want to use a mix of sounds from different packs
        bestoutput, bestmediamissingcount = None, len(tokens)
        for mediapack in self.mediapacks:
            log.info("Checking for reading in pack %s", mediapack.name)
            output, mediamissingcount = self.audioreadingforpack(mediapack, tokens)
            
            # We will end up choosing whatever pack minimizes the number of errors:
            if mediamissingcount < bestmediamissingcount:
                bestoutput, bestmediamissingcount = output, mediamissingcount
        
        # Did we get any result at all?
        if bestoutput:
            return bestoutput, (bestmediamissingcount != 0)
        else:
            return "", True


# Testsuite
if __name__=='__main__':
    import unittest
    import dictionary
    
    from media import MediaPack
    
    # Shared dictionary
    englishdict = Thunk(lambda: dictionary.PinyinDictionary.load("en"))
    
    # Default tone color list for tests
    colorlist = {
        1 : u"#ff0000",
        2 : u"#ffaa00",
        3 : u"#00aa00",
        4 : u"#0000ff",
        5 : u"#545454"
      }
    
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
            return Colorizer(colorlist).colorize(englishdict.reading(what)).flatten()
    
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
            return Colorizer(colorlist).colorize(englishdict.tonedchars(what)).flatten()
    
    class PinyinAudioReadingsTest(unittest.TestCase):
        default_raw_available_media = ["na3.mp3", "ma4.mp3", "xiao3.mp3", "ma3.mp3", "ci2.mp3", "dian3.mp3",
                                       "a4.mp3", "nin2.mp3", "ni3.ogg", "hao3.ogg", "gen1.ogg", "gen1.mp3"]
        
        def testRSuffix(self):
            self.assertHasReading(u"哪兒", "[sound:na3.mp3]")
        
        def testFifthTone(self):
            self.assertHasReading(u"的", "[sound:de5.mp3]", raw_available_media=["de5.mp3", "de.mp3", "de4.mp3"])
            self.assertHasReading(u"了", "[sound:le.mp3]", raw_available_media=["le4.mp3", "le.mp3"])
            self.assertHasReading(u"吗", "[sound:ma4.mp3]", raw_available_media=["ma4.mp3"])
        
        def testNv(self):
            self.assertHasReading(u"女", "[sound:nu:3.mp3]", raw_available_media=["nv3.mp3", "nu:3.mp3", "nu3.mp3"])
            self.assertHasReading(u"女", "[sound:nv3.mp3]", raw_available_media=["nu3.mp3", "nv3.mp3"])
            self.assertMediaMissing(u"女", raw_available_media=["nu3.mp3"])
            
        def testLv(self):
            self.assertHasReading(u"侣", "[sound:lv3.mp3]", raw_available_media=["lv3.mp3"])
            self.assertMediaMissing(u"侣", raw_available_media=["lu3.mp3"])
            self.assertHasReading(u"掠", "[sound:lve4.mp3]", raw_available_media=["lve4.mp3"])
            self.assertMediaMissing(u"掠", raw_available_media=["lue4.mp3"])
        
        def testJunkSkipping(self):
            self.assertHasPartialReading(u"Washington ! ! !", "")
        
        def testMultipleCharacters(self):
            self.assertHasReading(u"小马词典", "[sound:xiao3.mp3][sound:ma3.mp3][sound:ci2.mp3][sound:dian3.mp3]")
        
        def testMixedEnglishChinese(self):
            self.assertHasReading(u"啊 The Small 马 Dictionary", "[sound:a4.mp3][sound:ma3.mp3]")
        
        def testPunctuation(self):
            self.assertHasReading(u"您 (pr.)", "[sound:nin2.mp3]")
        
        def testSecondaryExtension(self):
            self.assertHasReading(u"你好", "[sound:ni3.ogg][sound:hao3.ogg]")
    
        def testMixedExtensions(self):
            self.assertHasReading(u"你马", "[sound:ni3.ogg][sound:ma3.mp3]")
    
        def testPriority(self):
            self.assertHasReading(u"根", "[sound:gen1.mp3]")
    
        def testMediaMissing(self):
            self.assertMediaMissing(u"根", raw_available_media=[".mp3"])
    
        def testCaptializationInPinyin(self):
            # NB: 上海 is in the dictionary with capitalized pinyin (Shang4 hai3)
            self.assertHasReading(u"上海", "[sound:shang4.mp3][sound:hai3.mp3]", raw_available_media=["shang4.mp3", "hai3.mp3"])
        
        def testCapitializationInFilesystem(self):
            self.assertHasReading(u"根", "[sound:GeN1.mP3]", available_media={"GeN1.mP3" : "GeN1.mP3" })
    
        def testDontMixPacks(self):
            packs = [MediaPack("Foo", {"ni3.mp3" : "ni3.mp3"}), MediaPack("Bar", {"hao3.mp3" : "hao3.mp3"})]
            self.assertHasPartialReading(u"你好", "[sound:ni3.mp3]", mediapacks=packs)
    
        def testUseBestPack(self):
            packs = [MediaPack("Foo", {"xiao3.mp3" : "xiao3.mp3", "ma3.mp3" : "ma3.mp3"}),
                     MediaPack("Bar", {"ma3.mp3" : "ma3.mp3", "ci2.mp3" : "ci2.mp3", "dian3.mp3" : "dian3.mp3"})]
            self.assertHasPartialReading(u"小马词典", "[sound:ma3.mp3][sound:ci2.mp3][sound:dian3.mp3]", mediapacks=packs)
    
        # Test helpers
        def assertHasReading(self, what, shouldbe, **kwargs):
            output, mediamissing = self.audioreading(what, **kwargs)
            self.assertFalse(mediamissing)
            self.assertEquals(output, shouldbe)
        
        def assertHasPartialReading(self, what, shouldbe, **kwargs):
            output, mediamissing = self.audioreading(what, **kwargs)
            self.assertTrue(mediamissing)
            self.assertEquals(output, shouldbe)
        
        def assertMediaMissing(self, what, **kwargs):
            output, mediamissing = self.audioreading(what, **kwargs)
            self.assertTrue(mediamissing)
        
        def audioreading(self, what, **kwargs):
            mediapacks = self.expandmediapacks(**kwargs)
            return PinyinAudioReadings(mediapacks, [".mp3", ".ogg"]).audioreading(englishdict.reading(what))
        
        def expandmediapacks(self, mediapacks=None, available_media=None, raw_available_media=default_raw_available_media):
            if mediapacks:
                return mediapacks
            elif available_media:
                return [MediaPack("Test", available_media)]
            else:
                return [MediaPack("Test", dict([(filename, filename) for filename in raw_available_media]))]
    
    unittest.main()
