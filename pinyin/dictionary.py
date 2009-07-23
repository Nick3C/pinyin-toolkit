#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import re

import sqlalchemy

from logger import log
from model import *
import meanings
from utils import *

"""
Encapsulates one or more Chinese dictionaries, and provides the ability to transform
strings of Hanzi into their pinyin equivalents.
"""
class PinyinDictionary(object):
    languagedicts = {
            'en'     : (1, "CEDICT"),
            'de'     : (0, "HanDeDict"),
            'fr'     : (0, "CFDICT")
        }
    
    # Regular expression used for pulling stuff out of the dictionary
    lineregex = re.compile(r"^([^#\s]+)\s+([^\s]+)\s+\[([^\]]+)\](\s+)?(.*)$")
    
    @classmethod
    def load(cls, language, dbconnect):
        # Default to the pinyin-only dictionary if this language doesn't have a dictionary.
        # DEBUG - this means that we will lose measure words for languages other than English - seperate the two
        langdata = cls.languagedicts.get(language, None)
        if langdata is None:
            (dicttablesimptradindex, languagedict), discardmeanings = cls.languagedicts['en'], True
        else:
            (dicttablesimptradindex, languagedict), discardmeanings = langdata, False
        
        log.info("Beginning load of dictionary for language code %s (%s)", language, languagedict)
        languagedicttable = sqlalchemy.Table(languagedict, dbconnect.metadata, autoload=True)
        charpinyintable = sqlalchemy.Table("CharacterPinyin", dbconnect.metadata, autoload=True)
        return PinyinDictionary(dbconnect, languagedicttable, charpinyintable, discardmeanings, dicttablesimptradindex,
                                ['pinyin_toolkit_sydict.u8', 'dict-userdict.txt'])
    
    def __init__(self, dbconnect, dicttable, charpinyintable, discardmeanings, dicttablesimptradindex, auxdictnames):
        # Save the dictionary table we will use for most lookups, and use it to initialize maximum character length
        self.__dbconnect = dbconnect
        self.__dicttable = dicttable
        self.__charpinyintable = charpinyintable
        self.__discardmeanings = discardmeanings
        self.__dicttablesimptradindex = dicttablesimptradindex
        self.__maxcharacterlen = max(dbconnect.selectScalar(sqlalchemy.func.max(sqlalchemy.func.length(dicttable.c.HeadwordSimplified))), 1)
        
        # Build the auxilliary dictionary, giving precedence to dictionaries later on in the input list
        self.__auxreadingsmeanings = FactoryDict(lambda _: [])
        for auxdictpath in [toolkitdir("pinyin", "dictionaries", auxdictname) for auxdictname in auxdictnames]:
            # Avoid loading auxilliary dictionaries that aren't there (e.g. the dict-userdict.txt if the user hasn't created it)
            if os.path.exists(auxdictpath):
                log.info("Loading auxilliary dictionary from %s", auxdictpath)
                self.loadsingledict(auxdictpath)
            else:
                log.warn("Skipping missing dictionary at %s", auxdictpath)
    
    def loadsingledict(self, auxdictpath):
        file = codecs.open(auxdictpath, "r", encoding='utf-8')
        try:
            for line in file:
                # Match this line
                m = self.lineregex.match(line)
                if not(m):
                    continue
                
                # Extract information from dictionary
                lcharacters = m.group(1)
                rcharacters = m.group(2)
                raw_pinyin = m.group(3)
                raw_definition = m.group(5)
                
                # Save meanings and readings
                for characters in [lcharacters, rcharacters]:
                    # Update the maximum character length
                    self.__maxcharacterlen = max(self.__maxcharacterlen, len(characters))
                    
                    # Save the readings and meanings for both simplified and traditional keys
                    self.__auxreadingsmeanings[characters].append((raw_pinyin, raw_definition))
        finally:
            file.close()

    """
    Given a string of Hanzi, return the result rendered into a list of Pinyin and unrecognised tokens (as strings).
    """
    def reading(self, sentence):
        log.info("Requested reading for %s", sentence)
        
        def addword(words, _text, readingtokens):
            # If we already have some text building up, add a preceding space.
            # However, if the word we got looks like a period, don't do it.
            # This ensures consistency in the treatment of Western and Chinese
            # punctuation.  Furthermore, avoid adding double-spaces.  This is
            # also important for punctuation consistency, because Western
            # punctuation is typically followed by a space whereas the Chinese
            # equivalents are not.
            words_need_space = needsspacebeforeappend(words)
            is_punctuation = ispunctuation(flatten(readingtokens))
            reading_starts_with_er = len(readingtokens) > 0 and readingtokens[0].iser
            if words_need_space and not(is_punctuation) and not(reading_starts_with_er):
                words.append(Word(Text(u' ')))
            
            # Add this reading into the token list with nice formatting
            words.append(Word.spacedwordfromunspacedtokens(readingtokens))
        
        return self.mapparsedtokens(sentence, addword)

    """
    Given a string of Hanzi, return the result rendered into a list of characters with tone information and unrecognised tokens (as string).
    """
    def tonedchars(self, sentence):
        log.info("Requested toned characters for %s", sentence)
        
        def addword(words, text, readingtokens):
            # Match up the reading data with the characters to produce toned characters
            words.append(Word(*(tonedcharactersfromreading(text, readingtokens))))
        
        return self.mapparsedtokens(sentence, addword)

    def mapparsedtokens(self, sentence, addword):
        # Represents the resulting stream of words
        words = []
        
        for readingsmeanings, text in self.parse(sentence):
            if readingsmeanings is None:
                # A single unrecognised character: it's probably just whitespace or punctuation.
                # Append it directly to the token list.
                words.append(Word(Text(text)))
            else:
                # Got a recognised token sequence! Hooray! Use the user-supplied function to add
                # the reading of this thing to the output
                addword(words, text, tokenizespaceseperated(readingsmeanings[0][0]))
        
        return words

    """
    Given a string of Hanzi, return meanings and measure words for the first recognisable thing in the string.
    If there is more than one recognisable thing then assume it is a phrase and don't return a meaning.
    """
    def meanings(self, sentence, prefersimptrad):
        log.info("Requested meanings for %s", sentence)
        
        # If we loaded a dictionary in the wrong language, then we shouldn't return
        # the English meanings from here or we will not fall back onto Google
        if self.__discardmeanings:
            return None, None
        
        isfirstparsedthing = True
        foundmeanings, foundmeasurewords = None, None
        for readingsmeanings, text in self.parse(sentence):
            if readingsmeanings is None and (ispunctuation(text.strip()) or text.strip() == u""):
                # Discard punctuation and whitespace from consideration, or we don't return a reading for e.g. "你好!"
                continue
            
            if not (isfirstparsedthing):
                # This is a phrase with more than one word - let someone else translate it
                # NB: apply this even if the first thing was an unrecognised bit of English,
                # see <http://github.com/batterseapower/pinyin-toolkit/issues/unreads#issue/71>.
                # We want to translate things like U盘 using Google rather than just returning "tray".
                log.info("We found a phrase, so returning no meanings")
                return None, None
            
            isfirstparsedthing = False
            
            if readingsmeanings is not None:
                # A recognised thing!  Find the definition in the dictionary:
                while len(readingsmeanings) > 0 and readingsmeanings[0][1][1] is None:
                    readingsmeanings.pop(0)
                
                # Did we actually have a non-null meaning in there?
                if len(readingsmeanings) == 0:
                    # NB: we return None if there is no meaning in the codomain. This case can
                    # occur if the character only comes
                    log.info("We found a reading but no meaning for some text")
                    return None, None
                else:
                    # We got a raw definition, but we need to clean up it before using it
                    simptradindex, meaning = readingsmeanings[0][1]
                    foundmeanings, foundmeasurewords = meanings.MeaningFormatter(simptradindex, prefersimptrad).parsedefinition(meaning, self.tonedchars)
                    
        return foundmeanings, foundmeasurewords

    def parse(self, sentence):
        assert type(sentence)==unicode
        if sentence == None or len(sentence) == 0:
            return
        
        # Strip HTML
        sentence = striphtml(sentence)
        
        # Iterate through the text
        i = 0;
        while i < len(sentence):
            # Try all possible word lengths (naive, but easy to code)
            found_something = False
            for word_len in range(self.__maxcharacterlen, 0, -1):
                candidate_word = sentence[i:i + word_len]
                readingmeanings = self.parseexact(candidate_word)
                if len(readingmeanings) > 0:
                    # A real word! Let's yield it immediately
                    yield (readingmeanings, candidate_word)
                    
                    # Continue looking for a new word after the end of this one
                    found_something = True
                    i += word_len
                    break
            
            if not(found_something):
                # Failed to find a single valid word in this text, so let's just yield
                # a single character token. TODO: yield multi-character tokens for efficiency.
                yield (None, sentence[i:i+1])
                i += 1
    
    # The readings and meanings returned for a word should correspond to each other,
    # and be returned in frequency order: most frequent first
    def parseexact(self, word):
        def zapempty(what):
            if what == "":
                return None
            else:
                return what
        
        # First port of call: the auxilliary dictionary. This contains user overrides,
        # which have priority overy absolutely everything else
        readingsmeanings = [(reading, (0, zapempty(meaning))) for reading, meaning in self.__auxreadingsmeanings[word]]
        
        # Now consider the main dictionary in the database (typically CEDICT):
        for reading, meaning in self.__dbconnect.selectRows(sqlalchemy.select(
                [self.__dicttable.c.Reading,
                 self.__dicttable.c.Translation],
                sqlalchemy.or_(self.__dicttable.c.HeadwordSimplified == word,
                               self.__dicttable.c.HeadwordTraditional == word))):
            if meaning == "":
                meaning = None
            readingsmeanings.append((reading, (self.__dicttablesimptradindex, zapempty(meaning))))
        
        # So far, we haven't applied any frequency information, but we can be a bit clever here and take
        # advantage of the fact that Unihan returns readings in frequency order to permute the list so far
        # TODO

        # Check Unihan as well:
        readingsmeanings.extend([(reading[0], None) for reading in self.__dbconnect.selectRows(sqlalchemy.select([self.__charpinyintable.c.Reading], self.__charpinyintable.c.ChineseCharacter == word))])
        
        return readingsmeanings

def combinemeaningsmws(dictmeanings, dictmeasurewords):
    if dictmeasurewords is not None and len(dictmeasurewords) > 0:
        return (dictmeanings or []) + [[Word(Text("MW: "))] + flattenmeasurewords(dictmeasurewords)]
    else:
        return dictmeanings

def flattenmeasurewords(dictmeasurewords):
    measurewordss = [charwords + [Word(Text(" - "))] + pinyinwords for (charwords, pinyinwords) in dictmeasurewords]
    return concat(intersperse([Word(Text(", "))], measurewordss))
