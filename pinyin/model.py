#!/usr/bin/env python
# -*- coding: utf-8 -*-

import htmlentitydefs
import re
import sqlalchemy
import unicodedata

from db import database
from logger import log
import utils


def opt_dict_arg_repr(dict):
    return len(dict) > 0 and ", " + repr(dict) or ""

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
    def __new__(cls, text, htmlattrs=None):
        if len(text) == 0:
            raise ValueError("All Text tokens must be non-empty")
        
        self = unicode.__new__(cls, text)
        self.htmlattrs = htmlattrs or {}
        return self

    iser = property(lambda self: False)

    def __repr__(self):
        return u"Text(%s%s)" % (unicode.__repr__(self), opt_dict_arg_repr(self.htmlattrs))

    def __eq__(self, other):
        if other is None or other.__class__ != self.__class__:
            return False
        
        return unicode.__eq__(other, self) and other.htmlattrs == self.htmlattrs
    
    def __ne__(self, other):
        return not(self == other)

    def accept(self, visitor):
        return visitor.visitText(self)

"""
Represents a single Pinyin character in the system.
"""
class Pinyin(object):
    # Extract a simple regex of all the possible pinyin.
    # NB: we have to delay-load  this in order to give the UI a chance to create the database if it is missing
    # NB: we only need to consider the ü versions because the regex is used to check *after* we have normalised to ü
    validpinyin = utils.Thunk(lambda: set(["r"] + [substituteForUUmlaut(pinyin[0]).lower() for pinyin in database.selectRows(sqlalchemy.select([sqlalchemy.Table("PinyinSyllables", database.metadata, autoload=True).c.Pinyin]))]))
    
    def __init__(self, word, toneinfo, htmlattrs=None):
        self.word = word
        
        if isinstance(toneinfo, int):
            # Convenience constructor: build a ToneInfo from a simple number
            self.toneinfo = ToneInfo(written=toneinfo)
        else:
            self.toneinfo = toneinfo
        
        self.htmlattrs = htmlattrs or {}
    
    iser = property(lambda self: self.word.lower() == u"r" and self.toneinfo.written == 5)

    def __str__(self):
        return self.__unicode__()
    
    def __unicode__(self):
        return self.numericformat(hideneutraltone=True)
    
    def __repr__(self):
        return u"Pinyin(%s, %s%s)" % (repr(self.word), repr(self.toneinfo), opt_dict_arg_repr(self.htmlattrs))
    
    def __eq__(self, other):
        if other == None or other.__class__ != self.__class__:
            return False
        
        return self.toneinfo == other.toneinfo and self.word == other.word and self.htmlattrs == other.htmlattrs
    
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
        if word.lower() not in cls.validpinyin():
            log.info("Couldn't find %s in the valid pinyin list", word)
            raise ValueError(u"The proposed pinyin '%s' doesn't look like pinyin after all" % text)
        
        # We now have a word and tone info, whichever route we took
        return Pinyin(word, toneinfo)

"""
Represents a Chinese character with tone information in the system.
"""
class TonedCharacter(unicode):
    def __new__(cls, character, toneinfo, htmlattrs=None):
        if len(character) == 0:
            raise ValueError("All TonedCharacters tokens must be non-empty")
        
        self = unicode.__new__(cls, character)
        
        if isinstance(toneinfo, int):
            # Convenience constructor
            self.toneinfo = ToneInfo(written=toneinfo)
        else:
            self.toneinfo = toneinfo
        
        self.htmlattrs = htmlattrs or {}
        return self
    
    def __repr__(self):
        return u"TonedCharacter(%s, %s%s)" % (unicode.__repr__(self), repr(self.toneinfo), opt_dict_arg_repr(self.htmlattrs))
    
    def __eq__(self, other):
        if other == None or other.__class__ != self.__class__:
            return False
        
        return unicode.__eq__(self, other) and self.toneinfo == other.toneinfo and self.htmlattrs == other.htmlattrs
    
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
def tokenizespaceseperatedtext(text):
    # Read the pinyin into the array: 
    return [tokenizeone(possible_token, forcenumeric=True) for possible_token in text.split()]

def tokenizeone(possible_token, forcenumeric=False):
    # Sometimes the pinyin field in CEDICT contains english (e.g. in the pinyin for 'T shirt')
    # so we better handle that by returning it as a Text token.
    try:
        return Pinyin.parse(possible_token, forcenumeric=forcenumeric)
    except ValueError:
        return Text(possible_token)

def tokenizeonewitherhua(possible_token, forcenumeric=False):
    # The intention here is that if we fail to parse something as pinyin
    # which has an 'r' suffix, then we'll try again without it:
    
    # TODO: be much smarter about parsing erhua. They can appear *inside* the pinyin too!
    
    # First attempt: parse as vanilla pinyin
    try:
        return [Pinyin.parse(possible_token, forcenumeric=forcenumeric)]
    except ValueError:
        pass
        
    if possible_token.lower().endswith("r"):
        # We might be able to parse as erhua
        try:
            return [Pinyin.parse(possible_token[:-1], forcenumeric=forcenumeric),
                    Pinyin(possible_token[-1], 5)]
        except ValueError:
            pass
    
    # Nope, we're just going to have to fail :(
    return [Text(possible_token)]

def tokenizetext(text, forcenumeric):
    # To recognise pinyin amongst the rest of the text, for now just look for maximal
    # sequences of alphanumeric characters as defined by Unicode. This should catch
    # the pinyin, its tone marks, tone numbers (if any) and allow umlauts.
    tokens = []
    for recognised, match in utils.regexparse(re.compile(u"(\w|:)+", re.UNICODE), text):
        if recognised:
            tokens.extend(tokenizeonewitherhua(match.group(0), forcenumeric=forcenumeric))
        else:
            tokens.append(Text(match))
    
    # TODO: could be much smarter about segmentation here. For example, we could use the
    # pinyin regex to split up run on groups of pinyin-like characters.
    return tokens

"""
Turns an arbitrary string containing pinyin and HTML into a sequence of tokens. Does its best
to seperate pinyin out from normal text, but no guarantees!
"""

def tokenize(html, forcenumeric=False):
    try:
        from BeautifulSoup import BeautifulSoup, Tag
    except ImportError, e:
        if utils.islinux():
            raise ImportError("Could not import the Beautiful Soup library! Since you are running on Linux, you may have to install it manually. Try running 'sudo apt-get install python-beautifulsoup' using the terminal.")
        else:
            raise e
    
    def extract_attr_maybe(attrs, attr, into, extractor):
        if attr not in attrs:
            return {}

        res = extractor(attrs[attr])
        if res is None:
            return {}

        (extracted, newattrval) = res
        if newattrval is not None:
            attrs[attr] = newattrval
        else:
            del attrs[attr]

        return { into : extracted }

    def take_dict_elem(dict, key):
        if key in dict:
            val = dict[key]
            del dict[key]
            return (val, dict)
        else:
            return None

    # Quick, dirty and wrong:
    def parse_style(style):
        intelligible = {}
        unintelligible = []
        for pair in style.split(";"):
            split = pair.split(":")
            if len(split) == 2:
                k, v = split
                intelligible[k.strip().lower()] = v
            else:
                unintelligible.append(pair)

        return (intelligible, unintelligible)

    def unparse_style(intelligible, unintelligible):
        return "; ".join([k + " : " + v for k, v in intelligible.items()] + unintelligible)

    # For now, we only worry about the color attribute in the span tag's style
    def take_style_val(key):
        def go(style):
            intelligible, unintelligible = parse_style(style)

            taken = take_dict_elem(intelligible, key)
            if taken is not None:
                value, intelligible = taken
            else:
                value = None

            return (value, unparse_style(intelligible, unintelligible))

        return go
        
    def contextify(attributesstack, what):
        # Get the most recent attributes to apply at this point in time
        current_attrs = {}
        for attrs in attributesstack:
            current_attrs.update(attrs)
        
        for k, v in current_attrs.items():
            what.htmlattrs[k] = v
        
        return what
    
    # Stateful recursive algorithm for consuming the parse tree: tokens accumulate in the 'tokens' list
    tokens = []
    def recurse(attributesstack, parent):
        for child in parent.contents:
            if not isinstance(child, Tag):
                tokens.extend([contextify(attributesstack, token) for token in tokenizetext(unicode(child), forcenumeric)])
            elif child.isSelfClosing:
                tokens.append(Text("<%s />" % child.name))
            else:
                if child.name.lower() == "span":
                    # It's more convenient if we can see the attributes as a dictionary,
                    # although we might e.g. drop duplicates
                    attrsdict = dict([(k.lower(), v) for k, v in child.attrs])
    
                    # This is why we're even at this party: we want to grab the style stuff out
                    thisattributesstack = attributesstack + [extract_attr_maybe(attrsdict, "style", "color", take_style_val("color"))]
        
                    # We are still interested in writing out the remainder of the <span> tag, in
                    # case it had other information in it (apart from the "style" attribute)
                    thisattrs = attrsdict.items()
                else:
                    thisattributesstack = attributesstack
                    thisattrs = child.attrs
            
                tokens.append(Text("<%s%s>" % (child.name, "".join([' %s="%s"' % (key, value) for key, value in thisattrs]))))
                recurse(thisattributesstack, child)
                tokens.append(Text("</%s>" % child.name))
    
    # This is it, chaps: let's munge that HTML!
    recurse([], BeautifulSoup(html))
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
    
    def extend(self, items):
        for item in items:
            self.append(item)
    
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
        self.wrapHtml(text, unicode(text))

    def visitPinyin(self, pinyin):
        self.wrapHtml(pinyin, self.tonify and pinyin.tonifiedformat() or unicode(pinyin))

    def visitTonedCharacter(self, tonedcharacter):
        self.wrapHtml(tonedcharacter, unicode(tonedcharacter))
    
    def wrapHtml(self, token, text):
        if "color" in token.htmlattrs:
            self.output += '<span style="color:%s">' % token.htmlattrs["color"]
            self.output += text
            self.output += '</span>'
        else:
            self.output += text

"""
Given words of reading tokens, formats them for display by inserting
spaces between pinyin while being smart about punctuation.
"""
def formatreadingfordisplay(words):
    visitor = FormatReadingForDisplayVisitor()
    return [word.concatmap(visitor) for word in words]

maybeSpace = lambda val: val and [Text(" ")] or []

class FormatReadingForDisplayVisitor(TokenVisitor):
    def __init__(self):
        self.haveprecedingspace = True
        self.haveprecedingpinyin = False
    
    def visitText(self, text):
        firstchar = text[0]
        firstcharactsasspace = firstchar.isspace() or (utils.ispunctuation(firstchar) and not(utils.isprespacedpunctuation(unicode(text))))
        needleadingspace = not self.haveprecedingspace and not firstcharactsasspace
        
        lastchar = text[-1]
        lastcharactsasspace = lastchar.isspace() or (utils.ispunctuation(lastchar) and not(utils.ispostspacedpunctuation(unicode(text))))
        self.haveprecedingspace = lastcharactsasspace
        self.haveprecedingpinyin = False
        
        return maybeSpace(needleadingspace) + [text]
    
    def visitPinyin(self, pinyin):
        # Being an erhua better not be significant for spacing purposes if we directly follow text, rather than pinyin
        needleadingspace = not self.haveprecedingspace and not (pinyin.iser and self.haveprecedingpinyin)
        self.haveprecedingspace = False
        self.haveprecedingpinyin = True
        
        return maybeSpace(needleadingspace) + [pinyin]
    
    def visitTonedCharacter(self, tonedcharacter):
        # Treat characters like normal text
        return self.visitText(tonedcharacter)

"""
Attempts to invert formatreadingfordisplay. For use when recovering
a clean set of tokens from user input.
"""
def unformatreadingfordisplay(words):
    visitor = UnformatReadingForDisplayVisitor()
    return [word.concatmap(visitor) for word in words]

class UnformatReadingForDisplayVisitor(TokenVisitor):
    def visitText(self, text):
        stripped = text.strip()
        return len(stripped) > 0 and [Text(stripped)] or []
    
    def visitPinyin(self, pinyin):
        return [pinyin]
    
    def visitTonedCharacter(self, tonedcharacter):
        return [tonedcharacter]

"""
Makes some tokens that faithfully represent the given characters
with tone information attached, if it is possible to extract it
from the corresponding pinyin tokens.
"""
def tonedcharactersfromreading(characters, words):
    try:
        visitor = TonedCharactersFromReadingVisitor(characters)
        words = [word.map(visitor) for word in words]
        if len(visitor.characters) > 0:
            raise TonedCharactersFromReadingException("We had some residual characters: " + visitor.characters)
        else:
            return words
    except TonedCharactersFromReadingException, e:
        # Fall back on the untoned characters
        log.warn("Couldn't produce toned characters for %s because: %s", characters, e)
        return [Word(Text(characters))]

class TonedCharactersFromReadingException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class TonedCharactersFromReadingVisitor(TokenVisitor):
    def __init__(self, characters):
        self.characters = characters
    
    def checkLength(self, needed):
        if len(self.characters) < needed:
            raise TonedCharactersFromReadingException("Length mismatch: %s vs %s" % (self.characters, needed))
    
    def checkToken(self, corresponding, token):
        # NFKC: apply the compatability decomposition, followed by the canonical composition.
        # The reason we do this is that some CEDICT characters are stored with double-width
        # Roman letters in the character columns, but normal ones in the reading, like so:
        # Ｕ盤 Ｕ盘 [U pan2] /USB flash drive/see also 閃存盤|闪存盘[shan3 cun2 pan2]/
        #
        # By putting the token into NFKC those crazy letters get turned into the normal ones
        # that we can see in the reading column, and this assertion passes.
        if corresponding != unicode(token) and unicodedata.normalize("NFKC", corresponding) != unicode(token):
            raise TonedCharactersFromReadingException("Character mismatch: %s vs %s" % (corresponding, unicode(token)))
        else:
            # NB: because the reading token may be one without the craziness, we need to make sure
            # we use the possibly-crazy form to produce a text token here:
            return Text(corresponding)

    def visitText(self, text):
        self.checkLength(len(text))
        corresponding_text, self.characters = utils.splitat(self.characters, len(text))
        return self.checkToken(corresponding_text, text)
    
    def visitPinyin(self, pinyin):
        self.checkLength(1)
        character, self.characters = utils.splitat(self.characters, 1)
        if character.isdecimal():
            # Avoid making the numbers from the supplementary dictionary into toned
            # things, because it confuses users :-)
            return Text(character)
        else:
            return TonedCharacter(character, pinyin.toneinfo)
    
    def visitTonedCharacter(self, tonedcharacter):
        self.checkLength(1)
        character, self.characters = utils.splitat(self.characters, 1)
        return self.checkToken(character, tonedcharacter)

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
