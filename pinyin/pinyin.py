#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Represents a single Pinyin character in the system.
"""
class Pinyin(object):
    # Controls whether the neutral tone is hidden in the representation of a pinyin
    # that comes out of __str__. Used to e.g. hide the tone on an 'r' suffix pinyin
    hideneutraltone = True
    
    """
    Constructs a Pinyin object from text representing a single character and numeric tone mark.
    Optionally also takes as an argument the character it originated from.
    
    >>> Pinyin("hen3")
    hen3
    
    >>> Pinyin("hen3", "很")
    hen3
    """
    def __init__(self, text, character=None):
        # Length check
        if len(text) < 2 or len(text) > 6:
            raise ValueError("The text '%s' was not the right length to be Pinyin - should be in the range 2 to 6 characters" % text)
        
        # Extract the tone number, ensuring that the thing at the end of the string is actually a number
        try:
            self.tone = int(text[-1:])
        except ValueError:
            raise ValueError("The text '%s' didn't end with a valid tone number" % text)
        
        # Find the word. NB: might think about doing lower() here, as some dictionary words have upper case
        # (e.g. proper names) and this screws with e.g. the tonification logic.
        self.word = text[:-1]
        
        # Save the underlying character
        self.character = character
    
    def __str__(self):
        return self.__unicode__()
    
    def __unicode__(self):
        return self.numericformat(hideneutraltone=self.hideneutraltone)
    
    def numericformat(self, hideneutraltone=False):
        if hideneutraltone and self.tone == 5:
            return self.word
        else:
            return self.word + str(self.tone)
    
    def tonifiedformat(self):
        return PinyinTonifier().tonify(self.numericFormat(hideneutraltone=False))

    # String compatability methods:
    def endswith(self, what):
        return self.__str__().endswith(what)

"""
Parser class to add diacritical marks to numbered pinyin.
* 2008 modifications by Brian Vaughan (http://brianvaughan.net)
* 2007 originaly version by Robert Yu (http://www.robertyu.com)

Inspired by Pinyin Joe's Word macro (http://pinyinjoe.com)
"""
class PinyinTonifier(object):
    # The pinyin tone mark placement rules come from http://www.pinyin.info/rules/where.html
    
    # map (final) constanant+tone to tone+constanant
    constTone2ToneConst = {
        'n1':'1n',   'n2':'2n',   'n3':'3n',   'n4':'4n',
        'ng1':'1ng', 'ng2':'2ng', 'ng3':'3ng', 'ng4':'4ng',
        'r1':'1r',   'r2':'2r',   'r3':'3r',   'r4':'4r'
    }

    #
    # map vowel+vowel+tone to vowel+tone+vowel
    vowelVowelTone2VowelToneVowel = {
        'ai1':'a1i', 'ai2':'a2i', 'ai3':'a3i', 'ai4':'a4i',
        'ao1':'a1o', 'ao2':'a2o', 'ao3':'a3o', 'ao4':'a4o',
        'ei1':'e1i', 'ei2':'e2i', 'ei3':'e3i', 'ei4':'e4i',
        'ou1':'o1u', 'ou2':'o2u', 'ou3':'o3u', 'ou4':'o4u'
    }

    # don't want "5"'s in output for neutral tone
    remove5thToneNumber = {
        'a5':u'a',
        'e5':u'e',
        'i5':u'i',
        'o5':u'o',
        'u5':u'u',
        'v5':u'\u01D6',
        'u:5':u'\u01D6',
        'n5':u'n',
        'g5':u'g',
        'r5':u'r'
    }

    # map vowel-number combination to unicode hex equivalent
    vowelTone2Unicode = {
        'a1':u'\u0101',  'a2':u'\u00e1',  'a3':u'\u01ce',  'a4':u'\u00e0',
        'e1':u'\u0113',  'e2':u'\u00e9',  'e3':u'\u011b',  'e4':u'\u00e8',
        'i1':u'\u012b',  'i2':u'\u00ed',  'i3':u'\u01d0',  'i4':u'\u00ec',
        'o1':u'\u014d',  'o2':u'\u00f3',  'o3':u'\u01d2',  'o4':u'\u00f2',
        'u1':u'\u016b',  'u2':u'\u00fa',  'u3':u'\u01d4',  'u4':u'\u00f9',
        'v1':u'\u01db',  'v2':u'\u01d8',  'v3':u'\u01da',  'v4':u'\u01dc',
        'u:1':u'\u01db', 'u:2':u'\u01d8', 'u:3':u'\u01da', 'u:4':u'\u01dc'
    }

    """
    Convert pinyin text with tone numbers to pinyin with diacritical marks
    over the appropriate vowel.

    In:   input text.  Must be unicode type.
    Out:  UTF-8 copy of the input, tone markers replaced with diacritical marks
          over the appropriate vowels

    >>> PinyinToneFixer().ConvertPinyinToneNumbers("xiao3 long2 tang1 bao1")
    "xiǎo lóng tāng bāo"
    """
    def tonify(self, line):
        assert type(line)==unicode
        
        # First transform: commute tone numbers over finals containing only constants
        for (x,y) in self.constTone2ToneConst.items():
            line = line.replace(x,y)

        # Second transform: for runs of two vowels with a following tone mark, move
        # the tone mark so it occurs directly afterwards the first vowel
        for (x,y) in self.vowelVowelTone2VowelToneVowel.items():
            line = line.replace(x,y)

        # Third transform: remove neutral tones ("5"s) for, e.g. qing sheng
        for (x,y) in self.remove5thToneNumber.items():
            line = line.replace(x,y)

        # Fourth transform: map vowel-tone mark combinations to the Unicode equivalents
        for (x,y) in self.vowelTone2Unicode.items():
            line = line.replace(x,y)

        return line

"""
Represents some pinyin and unknown text tokens as a list of strings and Pinyin objects.
"""
class Reading(list):
    """
    Utility function that takes a reading such as that output by the PinyinDictionary
    and flattens it into a normal Unicode string.
    """
    def flatten(self, tonify=False):
        flatreading = u""
        for token in self:
            flatreading += unicode(token)
    
        if tonify:
            return PinyinTonifier().tonify(flatreading)
        else:
            return flatreading

if __name__ == "__main__":
    import unittest
    
    class PinyinTonifierTest(unittest.TestCase):
        def testEasy(self):
            self.assertEquals(PinyinTonifier().tonify(u"Han4zi4 bu4 mie4, Zhong1guo2 bi4 wang2!"),
                              u"Hànzì bù miè, Zhōngguó bì wáng!")
        
        def testGreeting(self):
            self.assertEquals(PinyinTonifier().tonify(u"ni3 hao3, wo3 xi3 huan xue2 xi2 Han4 yu3. wo3 de Han4 yu3 shui3 ping2 hen3 di1."),
                              u"nǐ hǎo, wǒ xǐ huan xué xí Hàn yǔ. wǒ de Hàn yǔ shuǐ píng hěn dī.")
        
        def testObscure(self):
            self.assertEquals(PinyinTonifier().tonify(u"huai4"), u"huài")
    
    unittest.main()