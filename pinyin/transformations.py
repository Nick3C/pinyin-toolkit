#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pinyin import *

"""
Colorize readings according to the reading in the Pinyin.
* 2009 rewrites by Max Bolingbroke <batterseapower@hotmail.com>
* 2009 modifications by Nick Cook <nick@n-line.co.uk> (http://www.n-line.co.uk)
"""
class BaseColorizer(object):
    tonecolors = {
        1 : u"#ff0000",
        2 : u"#ffaa00",
        3 : u"#00aa00",
        4 : u"#0000ff",
        5 : u"#545454"
      }
     
    def colorize(self, reading):
        output = Reading()
        for token in reading:
            if type(token) == Pinyin:
                output.append(u'<span style="color:' + self.tonecolors.get(token.tone) + u'">')
                output.append(self.beingcolorized(token))
                output.append(u'</span>')
            else:
                output.append(token)
        
        return output
    
    def beingcolorized(self, pinyin):
        raise NotImplementedError("BaseColorizer.beingcolorized should be overriden in the subclass")

class PinyinColorizer(BaseColorizer):
    def beingcolorized(self, pinyin):
        # Output the unmodified pinyin reading
        return pinyin

class CharacterColorizer(BaseColorizer):
    def beingcolorized(self, pinyin):
        # Replace the pinyin with the underlying character
        return pinyin.character

"""
Output audio reading corresponding to a textual reading.
* 2009 rewrites by Max Bolingbroke <batterseapower@hotmail.com>
* 2009 modifications by Nick Cook <nick@n-line.co.uk> (http://www.n-line.co.uk)
"""
class PinyinAudioReadings(object):
    def __init__(self, available_media, audioextensions):
        self.available_media = available_media
        self.audioextensions = audioextensions
    
    def mediafor(self, basename):
        # Check all possible extensions in order of priority
        for extension in self.audioextensions:
            name = basename + extension
            if name in self.available_media:
                return name
        
        # No suitable media existed!
        return None
    
    def audioreading(self, reading):
        output = u""
        for token in reading:
            # Remove the 儿 （r) from pinyin [too complicated to handle automatically].
            # Also skip anything that doesn't look like pinyin, such as English words
            if type(token) != Pinyin or token.numericformat(hideneutraltone=False) == "r5":
                continue
            
            # Find path to suitable media
            media = self.mediafor(token.numericformat(hideneutraltone=False))
            if not(media) and token.tone == 5:
                # Sometimes we can replace tone 5 with 4 in order to deal with lack of '[xx]5.ogg's
                media = self.mediafor(token.word + '4')
            
            # If we've managed to find some media, we can put it into the output:
            if media:
                output += '[sound:' + media +']'
        
        return output


# Testsuite
if __name__=='__main__':
    import unittest
    import dictionary
    
    dictionary = dictionary.PinyinDictionary.load("English")
    
    class TestPinyinColorizer(unittest.TestCase):
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
            return PinyinColorizer().colorize(dictionary.reading(what)).flatten()
    
    class TestCharacterColorizer(unittest.TestCase):
        def testColorize(self):
            self.assertEqual(self.colorize(u"妈麻马骂吗"),
                u'<span style="color:#ff0000">妈</span> <span style="color:#ffaa00">麻</span> ' +
                u'<span style="color:#00aa00">马</span> <span style="color:#0000ff">骂</span> ' +
                u'<span style="color:#545454">吗</span>')
    
        def testMixedEnglishChinese(self):
            self.assertEqual(self.colorize(u'Small 小 - Horse'),
                u'Small <span style="color:#00aa00">小</span> - Horse')
        
        def testPunctuation(self):
            self.assertEqual(self.colorize(u'小小!'),
                u'<span style="color:#00aa00">小</span> <span style="color:#00aa00">小</span>!')
    
        # Test helpers
        def colorize(self, what):
            return CharacterColorizer().colorize(dictionary.reading(what)).flatten()
    
    class TestPinyinAudioReadings(unittest.TestCase):
        def testRSuffix(self):
            self.assertEqual(self.audioreading(u"哪兒"), "[sound:na3.mp3]")
        
        def testFifthTone(self):
            self.assertEqual(self.audioreading(u"吗"), "[sound:ma4.mp3]")
        
        def testJunkSkipping(self):
            self.assertEqual(self.audioreading(u"Washington ! ! !"), "")
        
        def testMultipleCharacters(self):
            self.assertEqual(self.audioreading(u"小马词典"), "[sound:xiao3.mp3][sound:ma3.mp3][sound:ci2.mp3][sound:dian3.mp3]")
        
        def testMixedEnglishChinese(self):
            self.assertEqual(self.audioreading(u"啊 The Small 马 Dictionary"), "[sound:a4.mp3][sound:ma3.mp3]")
        
        def testPunctuation(self):
            self.assertEqual(self.audioreading(u"您 (pr.)"), "[sound:nin2.mp3]")
        
        def testSecondaryExtension(self):
            self.assertEqual(self.audioreading(u"你好"), "[sound:ni3.ogg][sound:hao3.ogg]")
    
        def testMixedExtensions(self):
            self.assertEqual(self.audioreading(u"你马"), "[sound:ni3.ogg][sound:ma3.mp3]")
    
        def testPriority(self):
            self.assertEqual(self.audioreading(u"根"), "[sound:gen1.mp3]")
    
        # Test helpers
        def audioreading(self, what):
            available_media = ["na3.mp3", "ma4.mp3", "xiao3.mp3", "ma3.mp3", "ci2.mp3", "dian3.mp3",
                               "a4.mp3", "nin2.mp3", "ni3.ogg", "hao3.ogg", "gen1.ogg", "gen1.mp3"]
            return PinyinAudioReadings(available_media, [".mp3", ".ogg"]).audioreading(dictionary.reading(what))
    
    unittest.main()