#!/usr/bin/env python
# -*- coding: utf-8 -*-

import utils


# The basic data model is as follows:
#  * Text is represented as lists of Words
#  * Words contain lists of Tokens
#  * Tokens are either Text, Pinyin or TonedCharacters

"""
Represents a word boundary in the system, where the tokens inside represent a complete Chinese word.
"""
class Word(list):
    def __init__(self, *items):
        # Filter bad elements
        list.__init__(self, [item for item in items if item != None])
    
    def __repr__(self):
        return u"Word(%s)" % list.__repr__(self)[1:-1]
    
    def __str__(self):
        return unicode(self)
    
    def __unicode__(self):
        output = u"<"
        for n, token in enumerate(self):
            if n != 0:
                output += u", "
            output += unicode(token)
        
        return output + u">"
    
    def append(self, what):
        # Filter bad elements
        if what != None:
            list.append(self, what)
    
    def accept(self, visitor):
        for token in self:
            token.accept(visitor)
    
    def map(self, visitor):
        word = Word()
        for token in self:
            word.append(token.accept(visitor))
        return word
    
    def concatmap(self, visitor):
        word = Word()
        for token in self:
            for newtoken in token.accept(visitor):
                word.append(newtoken)
        return word
    
    @classmethod
    def spacedwordfromunspacedtokens(cls, reading_tokens):
        # Add the tokens to the word, with spaces between the components
        word = Word()
        reading_tokens_count = len(reading_tokens)
        for n, reading_token in enumerate(reading_tokens):
            # Don't add spaces if this is the first token or if we have an erhua
            if n != 0 and not(reading_token.iser):
                word.append(Text(u' '))

            word.append(reading_token)
        
        return word

"""
Turns a space-seperated string of pinyin and English into a list of tokens,
as best we can.
"""
def tokenize(text):
    # Read the pinyin into the array: sometimes this field contains
    # english (e.g. in the pinyin for 'T shirt') so we better handle that
    tokens = []
    for possible_token in text.split():
        try:
            tokens.append(Pinyin(possible_token))
        except ValueError:
            tokens.append(Text(possible_token))

    return tokens

"""
Represents a purely textual token.
"""
class Text(unicode):
    def __new__(cls, text):
        if len(text) == 0:
            raise ValueError("All Text tokens must be non-empty")
        
        return unicode.__new__(cls, text)

    iser = property(lambda self: False)

    def __repr__(self):
        return "Text(%s)" % unicode.__repr__(self)

    def accept(self, visitor):
        return visitor.visitText(self)

"""
Represents a single Pinyin character in the system.
"""
class Pinyin(object):
    """
    Constructs a Pinyin object from text representing a single character and numeric tone mark.
    
    >>> Pinyin("hen3")
    hen3
    
    >>> Pinyin("hen3", u"很")
    hen3
    """
    def __init__(self, text):
        # Length check (yes, you can get 7 character pinyin, such as zhuang1)
        if len(text) < 2 or len(text) > 7:
            raise ValueError("The text '%s' was not the right length to be Pinyin - should be in the range 2 to 7 characters" % text)
        
        # Extract the tone number, ensuring that the thing at the end of the string is actually a number
        try:
            self.tone = int(text[-1:])
        except ValueError:
            raise ValueError("The text '%s' didn't end with a valid tone number" % text)
        
        # Find the word. NB: might think about doing lower() here, as some dictionary words have upper case
        # (e.g. proper names) and this screws with e.g. the tonification logic.
        self.word = text[:-1]
    
    iser = property(lambda self: self.word == u"r" and self.tone == 5)

    def __str__(self):
        return self.__unicode__()
    
    def __unicode__(self):
        return self.numericformat(hideneutraltone=True)
    
    def __repr__(self):
        return "Pinyin(%s)" % repr(self.numericformat())
    
    def __eq__(self, other):
        if other == None:
            return False
        
        return self.tone == other.tone and self.word == other.word
    
    def __ne__(self, other):
        return not (self.__eq__(other))
    
    def accept(self, visitor):
        return visitor.visitPinyin(self)
    
    def numericformat(self, hideneutraltone=False):
        if hideneutraltone and self.tone == 5:
            return self.word
        else:
            return self.word + str(self.tone)
    
    def tonifiedformat(self):
        return PinyinTonifier().tonify(self.numericformat(hideneutraltone=False))

    # String compatability methods:
    def endswith(self, what):
        return self.__str__().endswith(what)

"""
Represents a Chinese character with tone information in the system.
"""
class TonedCharacter(unicode):
    def __new__(cls, character, tone):
        if len(character) == 0:
            raise ValueError("All TonedCharacters tokens must be non-empty")
        
        self = unicode.__new__(cls, character)
        self.tone = tone
        return self

    iser = property(lambda self: unicode(self) == u"儿" or unicode(self) == u"兒")

    def accept(self, visitor):
        return visitor.visitTonedCharacter(self)

"""
Visitor for all token objects.
"""
class TokenVisitor(object):
    def visitText(self, text):
        raise NotImplementedError("Got an unexpected text-like object %s", text)

    def visitPinyin(self, pinyin):
        raise NotImplementedError("Got an unexpected Pinyin object %s", pinyin)

    def visitTonedCharacter(self, tonedcharacter):
        raise NotImplementedError("Got an unexpected TonedCharacter object %s", tonedcharacter)

"""
Flattens the supplied tokens down into a single string.
"""
def flatten(words, tonify=False):
    visitor = FlattenTokensVisitor(tonify)
    for word in words:
        word.accept(visitor)
    return visitor.output

class FlattenTokensVisitor(TokenVisitor):
    def __init__(self, tonify):
        self.output = u""
        self.tonify = tonify

    def visitText(self, text):
        self.output += unicode(text)

    def visitPinyin(self, pinyin):
        if self.tonify:
            self.output += pinyin.tonifiedformat()
        else:
            self.output += unicode(pinyin)

    def visitTonedCharacter(self, tonedcharacter):
        self.output += unicode(tonedcharacter)

"""
Report whether the supplied list of words ends with a space
character. Used for producing pretty formatted output.
"""
def endswithspace(words):
    visitor = EndsWithSpaceVisitor()
    [word.accept(visitor) for word in words]
    return visitor.endswithspace

class EndsWithSpaceVisitor(TokenVisitor):
    def __init__(self):
        self.endswithspace = False
    
    def visitText(self, text):
        self.endswithspace = text.endswith(u" ")
    
    def visitPinyin(self, pinyin):
        self.endswithspace = False
    
    def visitTonedCharacter(self, tonedcharacter):
        self.endswithspace = tonedcharacter.endswith(u" ")

"""
Parser class to add diacritical marks to numbered pinyin.
* 2009 minor to deal with missing "v"/"u:" issue mod by Nick Cook (http://www.n-line.co.uk)
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
        
        # TODO: make the tonifier work for mixed case characters too
        #line = line.lower()
        
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


if __name__ == "__main__":
    import unittest
    
    class PinyinTest(unittest.TestCase):
        def testUnicode(self):
            self.assertEquals(unicode(Pinyin(u"hen3")), u"hen3")
        
        def testStr(self):
            self.assertEquals(str(Pinyin(u"hen3")), u"hen3")
        
        def testRepr(self):
            self.assertEquals(repr(Pinyin(u"hen3")), u"Pinyin(u'hen3')")
        
        def testStrNeutralTone(self):
            py = Pinyin(u"ma5")
            self.assertEquals(str(py), u"ma")
        
        def testNumericFormat(self):
            self.assertEquals(Pinyin(u"hen3").numericformat(), u"hen3")
            
        def testNumericFormatNeutralTone(self):
            self.assertEquals(Pinyin(u"ma5").numericformat(), u"ma5")
            self.assertEquals(Pinyin(u"ma5").numericformat(hideneutraltone=True), u"ma")
        
        def testTonifiedFormat(self):
            self.assertEquals(Pinyin(u"hen3").tonifiedformat(), u"hěn")
        
        def testTonifiedFormatNeutralTone(self):
            self.assertEquals(Pinyin(u"ma5").tonifiedformat(), u"ma")
        
        def testIsEr(self):
            self.assertTrue(Pinyin(u"r5").iser)
            self.assertFalse(Pinyin(u"r4").iser)
            self.assertFalse(Pinyin(u"er5").iser)
        
        def testEndsWith(self):
            self.assertTrue(Pinyin("ma5").endswith("ma"))
            self.assertFalse(Pinyin("ma5").endswith("a5"))
            self.assertTrue(Pinyin("hen3").endswith("en3"))
    
    class TextTest(unittest.TestCase):
        def testNonEmpty(self):
            self.assertRaises(ValueError, lambda: Text(u""))
        
        def testRepr(self):
            self.assertEquals(repr(Text(u"hello")), "Text(u'hello')")
        
        def testIsEr(self):
            self.assertFalse(Text("r5").iser)
    
    class WordTest(unittest.TestCase):
        def testAppendSingleReading(self):
            self.assertEquals(flatten([Word.spacedwordfromunspacedtokens([Pinyin(u"hen3")])]), u"hen3")

        def testAppendMultipleReadings(self):
            self.assertEquals(flatten([Word.spacedwordfromunspacedtokens([Pinyin(u"hen3"), Pinyin(u"ma5")])]), u"hen3 ma")
        
        def testAppendSingleReadingErhua(self):
            self.assertEquals(flatten([Word.spacedwordfromunspacedtokens([Pinyin(u"r5")])]), u"r")

        def testAppendMultipleReadingsErhua(self):
            self.assertEquals(flatten([Word.spacedwordfromunspacedtokens([Pinyin(u"hen3"), Pinyin(u"ma5"), Pinyin("r5")])]), u"hen3 mar")
        
        def testEquality(self):
            self.assertEquals(Word(Text(u"hello")), Word(Text(u"hello")))
            self.assertNotEquals(Word(Text(u"hello")), Word(Text(u"hallo")))
        
        def testRepr(self):
            self.assertEquals(repr(Word(Text(u"hello"))), "Word(Text(u'hello'))")
        
        def testStr(self):
            self.assertEquals(str(Word(Text(u"hello"))), u"<hello>")
            self.assertEquals(unicode(Word(Text(u"hello"))), u"<hello>")
            
        def testFilterNones(self):
            self.assertEquals(Word(None, Text("yes"), None, Text("no")), Word(Text("yes"), Text("no")))
        
        def testAppendNoneFiltered(self):
            word = Word(Text("yes"), Text("no"))
            word.append(None)
            self.assertEquals(word, Word(Text("yes"), Text("no")))
        
        def testAccept(self):
            output = []
            class Visitor(object):
                def visitText(self, text):
                    output.append(text)
                
                def visitPinyin(self, pinyin):
                    output.append(pinyin)
                
                def visitTonedCharacter(self, tonedcharacter):
                    output.append(tonedcharacter)
            
            Word(Text("Hi"), Pinyin("hen3"), TonedCharacter("a", 2), Text("Bye")).accept(Visitor())
            self.assertEqual(output, [Text("Hi"), Pinyin("hen3"), TonedCharacter("a", 2), Text("Bye")])
        
        def testMap(self):
            class Visitor(object):
                def visitText(self, text):
                    return Text("MEH")
                
                def visitPinyin(self, pinyin):
                    return Pinyin("meh3")
                
                def visitTonedCharacter(self, tonedcharacter):
                    return TonedCharacter("M", 2)
            
            self.assertEqual(Word(Text("Hi"), Pinyin("hen3"), TonedCharacter("a", 2), Text("Bye")).map(Visitor()),
                             Word(Text("MEH"), Pinyin("meh3"), TonedCharacter("M", 2), Text("MEH")))
        
        def testConcatMap(self):
            class Visitor(object):
                def visitText(self, text):
                    return []
                
                def visitPinyin(self, pinyin):
                    return [pinyin, pinyin]
                
                def visitTonedCharacter(self, tonedcharacter):
                    return [TonedCharacter("M", 2)]
            
            self.assertEqual(Word(Text("Hi"), Pinyin("hen3"), TonedCharacter("a", 2), Text("Bye")).concatmap(Visitor()),
                             Word(Pinyin("hen3"), Pinyin("hen3"), TonedCharacter("M", 2)))
    
    class TonedCharacterTest(unittest.TestCase):
        def testIsEr(self):
            self.assertTrue(TonedCharacter(u"儿", 5).iser)
            self.assertTrue(TonedCharacter(u"兒", 5).iser)
            self.assertFalse(TonedCharacter(u"化", 2).iser)

    class TokenizeTest(unittest.TestCase):
        def testFromSingleSpacedString(self):
            self.assertEquals([Pinyin(u"hen3")], tokenize(u"hen3"))

        def testFromMultipleSpacedString(self):
            self.assertEquals([Pinyin(u"hen3"), Pinyin(u"hao3")], tokenize(u"hen3 hao3"))

        def testFromSpacedStringWithEnglish(self):
            self.assertEquals([Text(u"T"), Pinyin(u"xu4")], tokenize(u"T xu4"))

    class PinyinTonifierTest(unittest.TestCase):
        def testEasy(self):
            self.assertEquals(PinyinTonifier().tonify(u"Han4zi4 bu4 mie4, Zhong1guo2 bi4 wang2!"),
                              u"Hànzì bù miè, Zhōngguó bì wáng!")

        def testObscure(self):
            self.assertEquals(PinyinTonifier().tonify(u"huai4"), u"huài")

        def testUpperCase(self):
            self.assertEquals(PinyinTonifier().tonify(u"Huai4"), u"Huài")
        
        def testGreeting(self):
            self.assertEquals(PinyinTonifier().tonify(u"ni3 hao3, wo3 xi3 huan xue2 xi2 Han4 yu3. wo3 de Han4 yu3 shui3 ping2 hen3 di1."),
                              u"nǐ hǎo, wǒ xǐ huan xué xí Hàn yǔ. wǒ de Hàn yǔ shuǐ píng hěn dī.")
    
    class FlattenTest(unittest.TestCase):
        def testFlatten(self):
            self.assertEquals(flatten([Word(Text(u'a ')), Word(Pinyin(u"hen3"), Text(u' b')), Word(Text(u"junk")), Word(Pinyin(u"ma5"))]),
                              u"a hen3 bjunkma")
            
        def testFlattenTonified(self):
            self.assertEquals(flatten([Word(Text(u'a ')), Word(Pinyin(u"hen3"), Text(u' b')), Word(Text(u"junk")), Word(Pinyin(u"ma5"))], tonify=True),
                              u"a hěn bjunkma")

    class EndsWithSpaceTest(unittest.TestCase):
        def testEmptyDoesntEndWithSpace(self):
            self.assertFalse(endswithspace([]))
        
        def testEndsWithSpace(self):
            self.assertTrue(endswithspace([Word(Text("hello "))]))
            self.assertTrue(endswithspace([Word(Text("hello"), Text(" "), Text("World"), Text(" "))]))
            self.assertFalse(endswithspace([Word(Text("hello"))]))
    
    unittest.main()