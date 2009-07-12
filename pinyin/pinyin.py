#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import unicodedata

from logger import log
import utils

# Generally helpful pinyin utilities

# Map tones to Unicode combining diacritical marks
# <http://en.wikipedia.org/wiki/Combining_diacritical_mark>
tonecombiningmarks = [
    u'\u0304', # Macron
    u'\u0301', # Acute
    u'\u030C', # Caron
    u'\u0300', # Grave
    u''        # Blank - 5th tone is trivial
]

def substituteForUUmlaut(inwhat):
    return inwhat.replace(u"u:", u"ü").replace(u"U:", u"ü".upper()) \
                 .replace(u"v", u"ü").replace(u"V", u"ü".upper())

def waysToSubstituteAwayUUmlaut(inwhat):
    strategy1 = inwhat.replace(u"ü", u"v").replace(u"Ü", u"V")
    strategy2 = inwhat.replace(u"ü", u"u:").replace(u"Ü", u"U:")
    
    if strategy1 == strategy2:
        # Equal strategies, so the initial string doesn't contain ü
        return None
    else:
        # It makes a difference!
        return [strategy1, strategy2]

# The basic data model is as follows:
#  * Text is represented as lists of Words
#  * Words contain lists of Tokens
#  * Tokens are either Text, Pinyin or TonedCharacters
#  * Pinyin and TonedCharacters contain some ToneInfo

# NB: we support the following standard tones:
#  1) Flat
#  2) Rising
#  3) Falling-rising
#  4) Falling
#  5) Neutral

"""
Represents the spoken and written tones of something in the system.
"""
class ToneInfo(object):
    def __init__(self, written=None, spoken=None):
        object.__init__(self)
        
        if written is None and spoken is None:
            raise ValueError("At least one of the tones supplied to ToneInfo must be non-None")
        
        # Default the written tone to the spoken one and vice-versa
        self.written = written or spoken
        self.spoken = spoken or written

    def __repr__(self):
        return u"ToneInfo(written=%s, spoken=%s)" % (repr(self.written), repr(self.spoken))
    
    def __eq__(self, other):
        if other is None or other.__class__ != self.__class__:
            return False
        
        return other.written == self.written and other.spoken == self.spoken
    
    def __ne__(self, other):
        return not(self == other)

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
        return u"Text(%s)" % unicode.__repr__(self)

    def accept(self, visitor):
        return visitor.visitText(self)

"""
Represents a single Pinyin character in the system.
"""
class Pinyin(object):
    # From <http://www.stud.uni-karlsruhe.de/~uyhc/zh-hans/node/108>. Should match all valid pinyin
    # while excluding most invalid pinyin. Compared to his blogpost, this has the fix for 'er' pinyin,
    # and can additionally deal with 'r', which crops up in CEDICT for erhua.
    validpinyin = re.compile(u"(?:(?:(?:(?:[bcdfghjklmnpqrstwxyz]|[zcs]h)(?:i(?:ao|[uae])?|u(?:ai|[iaeo])?|üe?))|(?:(?:(?:[bcdfghjklmnpqrstwxyz]|[zcs]h)|')?(?:a[oi]?|ei?|ou?)))(?:(?:ng|n|r)(?![aeo]))?)|r", re.IGNORECASE + re.UNICODE)
    
    def __init__(self, word, toneinfo):
        self.word = word
        
        if isinstance(toneinfo, int):
            # Convenience constructor: build a ToneInfo from a simple number
            self.toneinfo = ToneInfo(written=toneinfo)
        else:
            self.toneinfo = toneinfo
    
    iser = property(lambda self: self.word.lower() == u"r" and self.toneinfo.written == 5)

    def __str__(self):
        return self.__unicode__()
    
    def __unicode__(self):
        return self.numericformat(hideneutraltone=True)
    
    def __repr__(self):
        return u"Pinyin(%s, %s)" % (repr(self.word), repr(self.toneinfo))
    
    def __eq__(self, other):
        if other == None or other.__class__ != self.__class__:
            return False
        
        return self.toneinfo == other.toneinfo and self.word == other.word
    
    def __ne__(self, other):
        return not (self.__eq__(other))
    
    def accept(self, visitor):
        return visitor.visitPinyin(self)
    
    def numericformat(self, hideneutraltone=False, tone="written"):
        if hideneutraltone and getattr(self.toneinfo, tone) == 5:
            return self.word
        else:
            return self.word + str(getattr(self.toneinfo, tone))
    
    def tonifiedformat(self):
        return PinyinTonifier().tonify(self.numericformat(hideneutraltone=False))

    """
    Constructs a Pinyin object from text representing a single character and numeric tone mark
    or an embedded tone mark on one of the letters.
    
    >>> Pinyin.parse("hen3")
    hen3
    """
    @classmethod
    def parse(cls, text, forcenumeric=False):
        # Normalise u: and v: into umlauted version:
        # NB: might think about doing lower() here, as some dictionary words have upper case (e.g. proper names)
        text = substituteForUUmlaut(text)
        
        # Length check (yes, you can get 7 character pinyin, such as zhuang1.
        # If the u had an umlaut then it would be 8 'characters' to Python)
        if len(text) < 2 or len(text) > 8:
            raise ValueError(u"The text '%s' was not the right length to be Pinyin - should be in the range 2 to 7 characters" % text)
        
        # Does it look like we have a non-tonified string?
        if text[-1].isdigit():
            # Extract the tone number directly
            toneinfo = ToneInfo(written=int(text[-1]))
            word = text[:-1]
        elif forcenumeric:
            # Whoops. Should have been numeric but wasn't!
            raise ValueError(u"No tone mark present on purportely-numeric pinyin '%s'" % text)
        else:
            # Seperate combining marks (NFD = Normal Form Decomposed) so it
            # is easy to spot the combining marks
            text = unicodedata.normalize('NFD', text)
            
            # Remove the combining mark to get the tone
            toneinfo, word = None, text
            for n, tonecombiningmark in enumerate(tonecombiningmarks):
                if tonecombiningmark != "" and tonecombiningmark in text:
                    # Two marks on the same string is an error
                    if toneinfo != None:
                        raise ValueError(u"Too many combining tone marks on the input pinyin '%s'" % text)
                    
                    # Record the corresponding tone and remove the combining mark
                    toneinfo = ToneInfo(written=n+1)
                    word = word.replace(tonecombiningmark, "")
            
            # No combining mark? Fall back on the unmarked 5th tone
            if toneinfo == None:
                toneinfo = ToneInfo(written=5)
            
            # Recombine for consistency of comparisons in the application (everything else assumes NFC)
            word = unicodedata.normalize('NFC', word)
        
        # Sanity check to catch English/French/whatever that doesn't look like pinyin
        match = cls.validpinyin.match(word)
        if match is None or match.end() < len(word):
            raise ValueError(u"The proposed pinyin '%s' doesn't look like pinyin after all" % text)
        
        # We now have a word and tone info, whichever route we took
        return Pinyin(word, toneinfo)

"""
Represents a Chinese character with tone information in the system.
"""
class TonedCharacter(unicode):
    def __new__(cls, character, toneinfo):
        if len(character) == 0:
            raise ValueError("All TonedCharacters tokens must be non-empty")
        
        self = unicode.__new__(cls, character)
        
        if isinstance(toneinfo, int):
            # Convenience constructor
            self.toneinfo = ToneInfo(written=toneinfo)
        else:
            self.toneinfo = toneinfo
            
        return self
    
    def __eq__(self, other):
        if other == None or other.__class__ != self.__class__:
            return False
        
        return unicode.__eq__(self, other) and self.toneinfo == other.toneinfo
    
    def __ne__(self, other):
        return not(self == other)

    iser = property(lambda self: (unicode(self) == u"儿" or unicode(self) == u"兒") and self.toneinfo.written == 5)

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
Turns a space-seperated string of pinyin and English into a list of tokens,
as best we can.
"""
def tokenizespaceseperated(text):
    # Read the pinyin into the array: 
    return [tokenizeone(possible_token, forcenumeric=True) for possible_token in text.split()]

def tokenizeone(possible_token, forcenumeric=False):
    # Sometimes the pinyin field in CEDICT contains english (e.g. in the pinyin for 'T shirt')
    # so we better handle that by returning it as a Text token.
    try:
        return Pinyin.parse(possible_token, forcenumeric=forcenumeric)
    except ValueError:
        return Text(possible_token)

"""
Turns an arbitrary string containing pinyin into a sequence of tokens. Does its best
to seperate pinyin out from normal text, but no guarantees!
"""
def tokenize(text, forcenumeric=False):
    # To recognise pinyin amongst the rest of the text, for now just look for maximal
    # sequences of alphanumeric characters as defined by Unicode. This should catch
    # the pinyin, its tone marks, tone numbers (if any) and allow umlauts.
    tokens = []
    for recognised, match in utils.regexparse(re.compile(u"\w+", re.UNICODE), text):
        if recognised:
            tokens.append(tokenizeone(match.group(0), forcenumeric=forcenumeric))
        else:
            tokens.append(Text(match))
    
    # TODO: for robustness, we should explicitly parse around HTML tags
    
    # TODO: could be much smarter about segmentation here. For example, we could use the
    # pinyin regex to split up run on groups of pinyin-like characters.
    return tokens

"""
Represents a word boundary in the system, where the tokens inside represent a complete Chinese word.
"""
class Word(list):
    ACCEPTABLE_TOKEN_TYPES = [Text, Pinyin, TonedCharacter]
    
    def __init__(self, *items):
        for item in items:
            assert item is None or type(item) in Word.ACCEPTABLE_TOKEN_TYPES
        
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
    
    def append(self, item):
        assert item is None or type(item) in Word.ACCEPTABLE_TOKEN_TYPES
        
        # Filter bad elements
        if item != None:
            list.append(self, item)
    
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
def needsspacebeforeappend(words):
    visitor = NeedsSpaceBeforeAppendVisitor()
    [word.accept(visitor) for word in words]
    return visitor.needsspacebeforeappend

class NeedsSpaceBeforeAppendVisitor(TokenVisitor):
    def __init__(self):
        self.needsspacebeforeappend = False
    
    def visitText(self, text):
        lastchar = text[-1]
        self.needsspacebeforeappend = (not(lastchar.isspace()) and not(utils.ispunctuation(lastchar))) or utils.ispostspacedpunctuation(text)
    
    def visitPinyin(self, pinyin):
        self.needsspacebeforeappend = True
    
    def visitTonedCharacter(self, tonedcharacter):
        # Treat it like normal text
        self.visitText(tonedcharacter)

"""
Makes some tokens that faithfully represent the given characters
with tone information attached, if it is possible to extract it
from the corresponding pinyin tokens.
"""
def tonedcharactersfromreading(characters, reading_tokens):
    # If we can't associate characters with tokens on a one-to-one basis we had better give up
    if len(characters) != len(reading_tokens):
        log.warn("Couldn't produce toned characters for %s because there are a different number of reading tokens than characters", characters)
        return [Text(characters)]

    # Add characters to the tokens /without/ spaces between them, but with tone info
    tokens = []
    for character, reading_token in zip(characters, reading_tokens):
        # Avoid making the numbers from the supplementary dictionary into toned
        # things, because it confuses users :-)
        if hasattr(reading_token, "toneinfo") and not(character.isdecimal()):
            tokens.append(TonedCharacter(character, reading_token.toneinfo))
        else:
            # Sometimes the tokens do not have tones (e.g. in the translation for T-shirt)
            tokens.append(Text(character))
    
    return tokens

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
        u'([nNrR])([1234])'  : ur'\g<2>\g<1>',
        u'([nN][gG])([1234])': ur'\g<2>\g<1>'
    }

    #
    # map vowel+vowel+tone to vowel+tone+vowel
    vowelVowelTone2VowelToneVowel = {
        u'([aA])([iIoO])([1234])' : ur'\g<1>\g<3>\g<2>',
        u'([eE])([iI])([1234])'   : ur'\g<1>\g<3>\g<2>',
        u'([oO])([uU])([1234])'   : ur'\g<1>\g<3>\g<2>'
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
            line = re.sub(x, y, line)

        # Second transform: for runs of two vowels with a following tone mark, move
        # the tone mark so it occurs directly afterwards the first vowel
        for (x,y) in self.vowelVowelTone2VowelToneVowel.items():
            line = re.sub(x, y, line)

        # Third transform: map tones to the Unicode equivalent
        for (x,y) in enumerate(tonecombiningmarks):
            line = line.replace(str(x + 1), y)

        # Turn combining marks into real characters - saves us doing this in all the test (Python
        # unicode string comparison does not appear to normalise!! Very bad!)
        return unicodedata.normalize('NFC', line)


if __name__ == "__main__":
    import unittest
    
    class ToneInfoTest(unittest.TestCase):
        def testAccessors(self):
            ti = ToneInfo(written=1, spoken=2)
            self.assertEquals(ti.written, 1)
            self.assertEquals(ti.spoken, 2)
        
        def testRepr(self):
            self.assertEquals(repr(ToneInfo(written=1, spoken=2)), "ToneInfo(written=1, spoken=2)")
        
        def testDefaulting(self):
            self.assertEquals(ToneInfo(written=1), ToneInfo(written=1, spoken=1))
            self.assertEquals(ToneInfo(spoken=1), ToneInfo(written=1, spoken=1))
        
        def testEq(self):
            self.assertEquals(ToneInfo(written=1, spoken=3), ToneInfo(written=1, spoken=3))
            self.assertNotEquals(ToneInfo(written=1, spoken=3), ToneInfo(written=2, spoken=3))
            self.assertNotEquals(ToneInfo(written=1, spoken=3), ToneInfo(written=1, spoken=5))
        
        def testEqDissimilar(self):
            self.assertNotEquals(ToneInfo(written=1, spoken=3), "ToneInfo(written=1, spoken=3)")
            self.assertNotEquals("ToneInfo(written=1, spoken=3)", ToneInfo(written=1, spoken=3))
    
        def testMustBeNonEmpty(self):
            self.assertRaises(ValueError, lambda: ToneInfo())
    
    class PinyinTest(unittest.TestCase):
        def testConvenienceConstructor(self):
            self.assertEquals(Pinyin(u"hen", 3), Pinyin(u"hen", ToneInfo(written=3)))
        
        def testUnicode(self):
            self.assertEquals(unicode(Pinyin(u"hen", 3)), u"hen3")
        
        def testStr(self):
            self.assertEquals(str(Pinyin(u"hen", 3)), u"hen3")
        
        def testRepr(self):
            self.assertEquals(repr(Pinyin(u"hen", 3)), u"Pinyin(u'hen', ToneInfo(written=3, spoken=3))")
        
        def testStrNeutralTone(self):
            py = Pinyin(u"ma", 5)
            self.assertEquals(str(py), u"ma")
        
        def testNumericFormat(self):
            self.assertEquals(Pinyin(u"hen", 3).numericformat(), u"hen3")
        
        def testNumericFormatSelectTone(self):
            self.assertEquals(Pinyin(u"hen", ToneInfo(written=1, spoken=2)).numericformat(tone="written"), u"hen1")
            self.assertEquals(Pinyin(u"hen", ToneInfo(written=1, spoken=2)).numericformat(tone="spoken"), u"hen2")
            
        def testNumericFormatNeutralTone(self):
            self.assertEquals(Pinyin(u"ma", 5).numericformat(), u"ma5")
            self.assertEquals(Pinyin(u"ma", 5).numericformat(hideneutraltone=True), u"ma")
        
        def testTonifiedFormat(self):
            self.assertEquals(Pinyin(u"hen", 3).tonifiedformat(), u"hěn")
        
        def testTonifiedFormatNeutralTone(self):
            self.assertEquals(Pinyin(u"ma", 5).tonifiedformat(), u"ma")
        
        def testIsEr(self):
            self.assertTrue(Pinyin(u"r", 5).iser)
            self.assertTrue(Pinyin(u"R", 5).iser)
            self.assertFalse(Pinyin(u"r", 4).iser)
            self.assertFalse(Pinyin(u"er", 5).iser)
        
        def testParse(self):
            self.assertEquals(Pinyin.parse("ma1"), Pinyin("ma", 1))
            self.assertEquals(Pinyin.parse("ma2"), Pinyin("ma", 2))
            self.assertEquals(Pinyin.parse("ma3"), Pinyin("ma", 3))
            self.assertEquals(Pinyin.parse("ma4"), Pinyin("ma", 4))
            self.assertEquals(Pinyin.parse("ma5"), Pinyin("ma", 5))
        
        def testParseAdditions(self):
            self.assertEquals(Pinyin.parse("er5"), Pinyin("er", 5))
            self.assertEquals(Pinyin.parse("r2"), Pinyin("r", 2))
        
        def testParseShort(self):
            self.assertEquals(Pinyin.parse("a1"), Pinyin("a", 1))
        
        def testParseLong(self):
            self.assertEquals(Pinyin.parse("zhuang1"), Pinyin("zhuang", 1))
        
        def testParseNormalisesUmlaut(self):
            self.assertEquals(Pinyin.parse("nu:3"), Pinyin.parse(u"nü3"))
            self.assertEquals(Pinyin.parse("nU:3"), Pinyin.parse(u"nÜ3"))
            self.assertEquals(Pinyin.parse("nv3"), Pinyin.parse(u"nü3"))
            self.assertEquals(Pinyin.parse("nV3"), Pinyin.parse(u"nÜ3"))
        
        def testParseTonified(self):
            self.assertEquals(Pinyin.parse("chi1"), Pinyin.parse(u"chī"))
            self.assertEquals(Pinyin.parse("shi2"), Pinyin.parse(u"shí"))
            self.assertEquals(Pinyin.parse("xiao3"), Pinyin.parse(u"xiǎo"))
            self.assertEquals(Pinyin.parse("dan4"), Pinyin.parse(u"dàn"))
            self.assertEquals(Pinyin.parse("huan"), Pinyin.parse(u"huan"))
        
        def testParseRespectsOtherCombiningMarks(self):
            self.assertEquals(u"nü", unicode(Pinyin.parse(u"nü5")))
            self.assertEquals(u"nü", unicode(Pinyin.parse(u"nü")))
        
        def testParseForceNumeric(self):
            Pinyin.parse("chi")
            self.assertRaises(ValueError, lambda: Pinyin.parse("chi", forcenumeric=True))
        
        def testParseUnicode(self):
            self.assertEquals(repr(Pinyin.parse(u"nü3")), u"Pinyin(u'n\\xfc', ToneInfo(written=3, spoken=3))")
        
        def testRejectsPinyinWithMultipleToneMarks(self):
            self.assertRaises(ValueError, lambda: Pinyin.parse(u"xíǎo"))
        
        def testRejectsSingleNumbers(self):
            self.assertRaises(ValueError, lambda: Pinyin.parse(u"1"))
        
        def testRejectsNumbers(self):
            self.assertRaises(ValueError, lambda: Pinyin.parse(u"12345"))
        
        def testRejectsPinyinlikeEnglish(self):
            self.assertRaises(ValueError, lambda: Pinyin.parse("USB"))
    
    class TextTest(unittest.TestCase):
        def testNonEmpty(self):
            self.assertRaises(ValueError, lambda: Text(u""))
        
        def testRepr(self):
            self.assertEquals(repr(Text(u"hello")), "Text(u'hello')")
        
        def testEq(self):
            self.assertEquals(Text(u"hello"), Text(u"hello"))
            self.assertNotEquals(Text(u"hello"), Text(u"bye"))
        
        def testEqDissimilar(self):
            self.assertNotEquals(Text(u"hello"), 'Text(u"hello")')
            self.assertNotEquals('Text(u"hello")', Text(u"hello"))
        
        def testIsEr(self):
            self.assertFalse(Text("r5").iser)
    
    class WordTest(unittest.TestCase):
        def testAppendSingleReading(self):
            self.assertEquals(flatten([Word.spacedwordfromunspacedtokens([Pinyin.parse(u"hen3")])]), u"hen3")

        def testAppendMultipleReadings(self):
            self.assertEquals(flatten([Word.spacedwordfromunspacedtokens([Pinyin.parse(u"hen3"), Pinyin.parse(u"ma5")])]), u"hen3 ma")
        
        def testAppendSingleReadingErhua(self):
            self.assertEquals(flatten([Word.spacedwordfromunspacedtokens([Pinyin.parse(u"r5")])]), u"r")

        def testAppendMultipleReadingsErhua(self):
            self.assertEquals(flatten([Word.spacedwordfromunspacedtokens([Pinyin.parse(u"hen3"), Pinyin.parse(u"ma5"), Pinyin.parse("r5")])]), u"hen3 mar")
        
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
            
            Word(Text("Hi"), Pinyin.parse("hen3"), TonedCharacter("a", 2), Text("Bye")).accept(Visitor())
            self.assertEqual(output, [Text("Hi"), Pinyin.parse("hen3"), TonedCharacter("a", 2), Text("Bye")])
        
        def testMap(self):
            class Visitor(object):
                def visitText(self, text):
                    return Text("MEH")
                
                def visitPinyin(self, pinyin):
                    return Pinyin.parse("hai3")
                
                def visitTonedCharacter(self, tonedcharacter):
                    return TonedCharacter("M", 2)
            
            self.assertEqual(Word(Text("Hi"), Pinyin.parse("hen3"), TonedCharacter("a", 2), Text("Bye")).map(Visitor()),
                             Word(Text("MEH"), Pinyin.parse("hai3"), TonedCharacter("M", 2), Text("MEH")))
        
        def testConcatMap(self):
            class Visitor(object):
                def visitText(self, text):
                    return []
                
                def visitPinyin(self, pinyin):
                    return [pinyin, pinyin]
                
                def visitTonedCharacter(self, tonedcharacter):
                    return [TonedCharacter("M", 2)]
            
            self.assertEqual(Word(Text("Hi"), Pinyin.parse("hen3"), TonedCharacter("a", 2), Text("Bye")).concatmap(Visitor()),
                             Word(Pinyin.parse("hen3"), Pinyin.parse("hen3"), TonedCharacter("M", 2)))
    
    class TonedCharacterTest(unittest.TestCase):
        def testConvenienceConstructor(self):
            self.assertEquals(TonedCharacter(u"儿", 2), TonedCharacter(u"儿", ToneInfo(written=2)))
        
        def testEq(self):
            self.assertEquals(TonedCharacter(u"儿", 2), TonedCharacter(u"儿", 2))
            self.assertNotEquals(TonedCharacter(u"儿", 2), TonedCharacter(u"儿", 3))
            self.assertNotEquals(TonedCharacter(u"儿", 2), TonedCharacter(u"兒", 2))
        
        def testEqDissimilar(self):
            self.assertNotEquals(TonedCharacter(u"儿", 2), "TonedCharacter(u'儿', 2)")
            self.assertNotEquals("TonedCharacter(u'儿', 2)", TonedCharacter(u"儿", 2))
        
        def testIsEr(self):
            self.assertTrue(TonedCharacter(u"儿", 5).iser)
            self.assertTrue(TonedCharacter(u"兒", 5).iser)
            self.assertFalse(TonedCharacter(u"化", 2).iser)
            self.assertFalse(TonedCharacter(u"儿", 4).iser)

    class TokenizeSpaceSeperatedTest(unittest.TestCase):
        def testFromSingleSpacedString(self):
            self.assertEquals([Pinyin.parse(u"hen3")], tokenizespaceseperated(u"hen3"))

        def testFromMultipleSpacedString(self):
            self.assertEquals([Pinyin.parse(u"hen3"), Pinyin.parse(u"hao3")], tokenizespaceseperated(u"hen3 hao3"))

        def testFromSpacedStringWithEnglish(self):
            self.assertEquals([Text(u"T"), Pinyin.parse(u"xu4")], tokenizespaceseperated(u"T xu4"))

        def testFromSpacedStringWithPinyinlikeEnglish(self):
            self.assertEquals([Text(u"USB"), Pinyin.parse(u"xu4")], tokenizespaceseperated(u"USB xu4"))

    class TokenizeTest(unittest.TestCase):
        def testTokenizeSimple(self):
            self.assertEquals([Pinyin.parse(u"hen3"), Text(" "), Pinyin.parse(u"hao3")], tokenize(u"hen3 hao3"))
            self.assertEquals([Pinyin.parse(u"hen3"), Text(","), Pinyin.parse(u"hao3")], tokenize(u"hen3,hao3"))
            self.assertEquals([Pinyin.parse(u"hen3"), Text(" "), Pinyin.parse(u"hao3"), Text(", "), Text("my"), Text(" "), Pinyin.parse(u"xiǎo"), Text(" "), Text("one"), Text("!")],
                              tokenize(u"hen3 hao3, my xiǎo one!"))
        
        def testTokenizeForceNumeric(self):
          self.assertEquals([Pinyin.parse(u"hen3"), Text(" "), Pinyin.parse(u"hao3")], tokenize(u"hen3 hao3"))
          self.assertEquals([Pinyin.parse(u"hen3"), Text(" "), Pinyin.parse(u"hao3"), Text(", "), Text("my"), Text(" "), Text(u"xiǎo"), Text(" "), Text("one"), Text("!")],
                            tokenize(u"hen3 hao3, my xiǎo one!", forcenumeric=True))
        
        def testTokenizeHTML(self):
            self.assertEquals([Text(u'<'), Text(u'span'), Text(u' '), Text(u'style'), Text(u'="'), Text(u'color'), Text(u':#'), Text(u'123456'), Text(u'">'),
                               Pinyin(u'tou', ToneInfo(written=2, spoken=2)), Text(u'</'), Text(u'span'), Text(u'> <'), Text(u'span'), Text(u' '), Text(u'style'),
                               Text(u'="'), Text(u'color'), Text(u':#'), Text(u'123456'), Text(u'">'), Pinyin(u'er', ToneInfo(written=4, spoken=4)), Text(u'</'), Text(u'span'), Text(u'>')],
                               tokenize(u'<span style="color:#123456">tou2</span> <span style="color:#123456">er4</span>'))

    class PinyinTonifierTest(unittest.TestCase):
        def testEasy(self):
            self.assertEquals(PinyinTonifier().tonify(u"Han4zi4 bu4 mie4, Zhong1guo2 bi4 wang2!"),
                              u"Hànzì bù miè, Zhōngguó bì wáng!")

        def testObscure(self):
            self.assertEquals(PinyinTonifier().tonify(u"huai4"), u"huài")

        def testUpperCase(self):
            self.assertEquals(PinyinTonifier().tonify(u"Huai4"), u"Huài")
            self.assertEquals(PinyinTonifier().tonify(u"An1 hui1 sheng3"), u"Ān huī shěng")
        
        def testGreeting(self):
            self.assertEquals(PinyinTonifier().tonify(u"ni3 hao3, wo3 xi3 huan xue2 xi2 Han4 yu3. wo3 de Han4 yu3 shui3 ping2 hen3 di1."),
                              u"nǐ hǎo, wǒ xǐ huan xué xí Hàn yǔ. wǒ de Hàn yǔ shuǐ píng hěn dī.")
    
    class FlattenTest(unittest.TestCase):
        def testFlatten(self):
            self.assertEquals(flatten([Word(Text(u'a ')), Word(Pinyin.parse(u"hen3"), Text(u' b')), Word(Text(u"junk")), Word(Pinyin.parse(u"ma5"))]),
                              u"a hen3 bjunkma")
            
        def testFlattenTonified(self):
            self.assertEquals(flatten([Word(Text(u'a ')), Word(Pinyin.parse(u"hen3"), Text(u' b')), Word(Text(u"junk")), Word(Pinyin.parse(u"ma5"))], tonify=True),
                              u"a hěn bjunkma")
        
        def testUsesWrittenTone(self):
            self.assertEquals(flatten([Word(Pinyin("hen", ToneInfo(written=2,spoken=3)))]), "hen2")

    class NeedsSpaceBeforeAppendTest(unittest.TestCase):
        def testEmptyDoesntNeedSpace(self):
            self.assertFalse(needsspacebeforeappend([]))
        
        def testEndsWithWhitespace(self):
            self.assertFalse(needsspacebeforeappend([Word(Text("hello "))]))
            self.assertFalse(needsspacebeforeappend([Word(Text("hello"), Text(" "), Text("World"), Text(" "))]))
            self.assertFalse(needsspacebeforeappend([Word(Text("hello"), Text(" "), Text("World"), Text("!\t"))]))
        
        def testNeedsSpace(self):
            self.assertTrue(needsspacebeforeappend([Word(Text("hello"))]))
        
        def testPunctuation(self):
            self.assertTrue(needsspacebeforeappend([Word(Text("."))]))
            self.assertTrue(needsspacebeforeappend([Word(Text(","))]))
            self.assertFalse(needsspacebeforeappend([Word(Text("("))]))
            self.assertFalse(needsspacebeforeappend([Word(Text(")"))]))
    
    class TonedCharactersFromReadingTest(unittest.TestCase):
        def testTonedTokens(self):
            self.assertEquals(tonedcharactersfromreading(u"一个", [Pinyin.parse("yi1"), Pinyin.parse("ge4")]),
                              [TonedCharacter(u"一", 1), TonedCharacter(u"个", 4)])

        def testTonedTokensWithoutTone(self):
            self.assertEquals(tonedcharactersfromreading(u"T恤", [Text("T"), Pinyin.parse("zhi4")]),
                              [Text(u"T"), TonedCharacter(u"恤", 4)])

        def testTonedTokenNumbers(self):
            self.assertEquals(tonedcharactersfromreading(u"1994", [Pinyin.parse("yi1"), Pinyin.parse("jiu3"), Pinyin.parse("jiu3"), Pinyin.parse("si4")]),
                              [Text(u"1"), Text(u"9"), Text(u"9"), Text(u"4")])
        
        def testTonesDontMatchChars(self):
            self.assertEquals(tonedcharactersfromreading(u"ABCD", [Pinyin.parse("yi1"), Pinyin.parse("shi2"), Pinyin.parse("jiu3"), Pinyin.parse("jiu3"), Pinyin.parse("shi2"), Pinyin.parse("si4")]),
                              [Text(u"ABCD")])

    
    unittest.main()