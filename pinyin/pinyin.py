#!/usr/bin/env python
# -*- coding: utf-8 -*-

import utils


"""
Represents a word boundary in the system, where the tokens inside represent a complete Chinese word.
"""
class Word(object):
    def __init__(self, token):
        self.token = token
    
    def __eq__(self, other):
        if other is None:
            return False
        
        return self.token == other.token
    
    def __ne__(self, other):
        return not(self == other)
    
    def __repr__(self):
        return u"Word(%s)" % repr(self.token)
    
    def __str__(self):
        return unicode(self)
    
    def __unicode__(self):
        return u"<%s>" % unicode(self.token)
    
    def accept(self, visitor):
        return visitor.visitWord(self)
    
    @classmethod
    def spacedwordreading(cls, reading_tokens):
        # Add the tokens to the tokens, with spaces between the components
        tokens = TokenList()
        reading_tokens_count = len(reading_tokens)
        for n, reading_token in enumerate(reading_tokens):
            # Don't add spaces if this is the first token or if we are at the
            # last token and have an erhua
            iser = hasattr(reading_token, "iser") and reading_token.iser
            if n != 0 and (n != reading_tokens_count - 1 or not(iser)):
                tokens.append(Text(u' '))

            tokens.append(reading_token)
        
        # Put the tokens together along with a Word marker
        return Word(tokens)
    
    # String compatability method
    def endswith(self, what):
        return self.token.endswith(what)


"""
Represents a single Pinyin character in the system.
"""
class Pinyin(object):
    # Controls whether the neutral tone is hidden in the representation of a pinyin
    # that comes out of __str__. Used to e.g. hide the tone on an 'r' suffix pinyin
    hideneutraltone = True
    
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
        return self.numericformat(hideneutraltone=self.hideneutraltone)
    
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
Represents a purely textual token.
"""
class Text(unicode):
    def __new__(cls, text):
        if len(text) == 0:
            raise ValueError("All Text tokens must be non-empty")
        
        return unicode.__new__(cls, text)

    def accept(self, visitor):
        return visitor.visitText(self)

"""
Represents some pinyin and unknown text tokens as a list of strings and Pinyin objects.
"""
class TokenList(list):
    def __init__(self, items=[]):
        # Filter bad elements
        list.__init__(self, [item for item in items if item != None])
    
    def accept(self, visitor):
        return visitor.visitTokenList(self)
    
    def append(self, what):
        # Filter bad elements
        if what != None:
            list.append(self, what)
    
    @classmethod
    def fromspacedstring(cls, raw_pinyin):
        # Read the pinyin into the array: sometimes this field contains
        # english (e.g. in the pinyin for 'T shirt') so we better handle that
        tokens = TokenList()
        for the_raw_pinyin in raw_pinyin.split():
            try:
                tokens.append(Pinyin(the_raw_pinyin))
            except ValueError:
                tokens.append(Text(the_raw_pinyin))

        # Special treatment for the erhua suffix: never show the tone in the string representation.
        # NB: currently hideneutraltone defaults to True, so this is sort of pointless.
        last_token = tokens[-1]
        if type(last_token) == Pinyin and last_token.iser:
            last_token.hideneutraltone = True

        return tokens

    # String compatability method
    def endswith(self, what):
        return self[-1].endswith(what)

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

    def visitWord(self, word):
        raise NotImplementedError("Got an unexpected Word object %s", word)

    def visitTokenList(self, tokens):
        raise NotImplementedError("Got an unexpected TokenList object %s", tokens)

"""
Visitor for token objects that looks through Words and TokenLists.
"""
class LeafTokenVisitor(TokenVisitor):
    def visitWord(self, word):
        return word.token.accept(self)
    
    def visitTokenList(self, tokens):
        for token in tokens:
            token.accept(self)

"""
Visitor for token objects that looks through and rebuilds Words and TokenLists.
"""
class MapTokenVisitor(TokenVisitor):
    def visitWord(self, word):
        return Word(word.token.accept(self))
    
    def visitTokenList(self, tokens):
        newtokens = TokenList()
        for token in tokens:
            newtokens.append(token.accept(self))
        return newtokens

# Convenience wrapper around the FlattenTokensVisitor
def flatten(token, tonify=False):
    visitor = FlattenTokensVisitor(tonify)
    token.accept(visitor)
    return visitor.output

"""
Flattens the supplied tokens down into a single string.
"""
class FlattenTokensVisitor(LeafTokenVisitor):
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
            
            # Since the default is to hide neutral tones, this doesn't do anything yet
            py.hideneutraltone = True
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
    
    class WordTest(unittest.TestCase):
        def testAppendSingleReading(self):
            self.assertEquals(flatten(Word.spacedwordreading([Pinyin(u"hen3")])), u"hen3")

        def testAppendMultipleReadings(self):
            self.assertEquals(flatten(Word.spacedwordreading([Pinyin(u"hen3"), Pinyin(u"ma5")])), u"hen3 ma")
        
        def testAppendSingleReadingErhua(self):
            self.assertEquals(flatten(Word.spacedwordreading([Pinyin(u"r5")])), u"r")

        def testAppendMultipleReadingsErhua(self):
            self.assertEquals(flatten(Word.spacedwordreading([Pinyin(u"hen3"), Pinyin(u"ma5"), Pinyin("r5")])), u"hen3 mar")
    
        def testEndsWith(self):
            self.assertTrue(Word(Text(u"hello")).endswith(u"lo"))
            self.assertFalse(Word(Text(u"hello")).endswith(u"ol"))
        
        def testEquality(self):
            self.assertEquals(Word(Text(u"hello")), Word(Text(u"hello")))
            self.assertNotEquals(Word(Text(u"hello")), Word(Text(u"hallo")))
        
        def testRepr(self):
            self.assertEquals(repr(Word(Text(u"hello"))), 'Word(Text(u"hello"))')
        
        def testStr(self):
            self.assertEquals(str(Word(Text(u"hello"))), u"<hello>")
            self.assertEquals(unicode(Word(Text(u"hello"))), u"<hello>")
    
    class TonedCharacterTest(unittest.TestCase):
        def testIsEr(self):
            self.assertTrue(TonedCharacter(u"儿", 5).iser)
            self.assertTrue(TonedCharacter(u"兒", 5).iser)
            self.assertFalse(TonedCharacter(u"化", 2).iser)

    class TokenListTest(unittest.TestCase):
        def testFilterNones(self):
            self.assertEquals(TokenList([None, Text("yes"), None, Text("no")]), TokenList([Text("yes"), Text("no")]))
        
        def testAppendNoneFiltered(self):
            tokens = TokenList([Text("yes"), Text("no")])
            tokens.append(None)
            self.assertEquals(tokens, TokenList([Text("yes"), Text("no")]))

        # TODO: test handling of erhua in append

        def testFromSingleSpacedString(self):
            self.assertEquals(TokenList([Pinyin(u"hen3")]), TokenList.fromspacedstring(u"hen3"))

        def testFromMultipleSpacedString(self):
            self.assertEquals(TokenList([Pinyin(u"hen3"), Pinyin(u"hao3")]), TokenList.fromspacedstring(u"hen3 hao3"))

        def testFromSpacedStringWithEnglish(self):
            self.assertEquals(TokenList([Text(u"T"), Pinyin(u"xu4")]), TokenList.fromspacedstring(u"T xu4"))

        def testEmpty(self):
            self.assertEquals(TokenList(), TokenList([]))
        
        def testEndsWith(self):
            self.assertTrue(TokenList([Text(u"hello")]).endswith(u"lo"))
            self.assertFalse(TokenList([Text(u"hello")]).endswith(u"ol"))

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
            self.assertEquals(flatten(TokenList([Text(u'a '), Pinyin(u"hen3"), Text(u' b'), Word(Text(u"junk")), Pinyin(u"ma5")])),
                              u"a hen3 bjunkma")
            
        def testFlattenTonified(self):
            self.assertEquals(flatten(TokenList([Text(u'a '), Pinyin(u"hen3"), Text(u' b'), Word(Text(u"junk")), Pinyin(u"ma5")]), tonify=True),
                              u"a hěn bjunkma")
    
    unittest.main()