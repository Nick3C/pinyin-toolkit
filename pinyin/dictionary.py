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


def parseMeaning(meaning, simptradindex):
    meaning = zapempty(meaning)
    if meaning is None:
        return None
    
    return lambda prefersimptrad, tonedcharscallback: meanings.MeaningFormatter(simptradindex, prefersimptrad).parsedefinition(meaning, tonedcharscallback)

def fileSource(dictname):
    filename = toolkitdir("pinyin", "dictionaries", dictname)
    
    # Avoid loading auxilliary dictionaries that aren't there (e.g. the dict-userdict.txt if the user hasn't created it)
    if not(os.path.exists(filename)):
        log.warn("Skipping missing dictionary at %s", filename)
        return None
    
    log.info("Loading file-based dictionary from %s", filename)
    file = codecs.open(filename, "r", encoding='utf-8')
    try:
        readingsmeanings = FactoryDict(lambda _: [])
        maxcharacterlen = 0
        for line in file:
            # Match this line
            m = PinyinDictionary.lineregex.match(line)
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
                maxcharacterlen = max(maxcharacterlen, len(characters))
                
                # Save the readings and meanings for both simplified and traditional keys
                readingsmeanings[characters].append((raw_pinyin, raw_definition))
    finally:
        file.close()
    
    return maxcharacterlen, lambda word: [(reading, parseMeaning(meaning, 0)) for reading, meaning in readingsmeanings[word]]

def databaseDictionarySource(dbconnect, tablename, simptradindex):
    log.info("Loading full dictionary from database table %s", tablename)
    
    dicttable = sqlalchemy.Table(tablename, dbconnect.metadata, autoload=True)
    maxcharacterlen = dbconnect.selectScalar(sqlalchemy.func.max(sqlalchemy.func.length(dicttable.c.HeadwordSimplified)))
    
    def inner(word):
        for reading, meaning in dbconnect.selectRows(sqlalchemy.select(
                [dicttable.c.Reading,
                 dicttable.c.Translation],
                sqlalchemy.or_(dicttable.c.HeadwordSimplified == word,
                               dicttable.c.HeadwordTraditional == word))):
            yield (reading, parseMeaning(meaning, simptradindex))
    
    return maxcharacterlen, inner

def databaseReadingSource(dbconnect):
    log.info("Loading character reading database")
    
    readingtable = sqlalchemy.Table("CharacterPinyin", dbconnect.metadata, autoload=True)
    
    return 1, lambda word: [(reading[0], None) for reading in dbconnect.selectRows(sqlalchemy.select([readingtable.c.Reading], readingtable.c.ChineseCharacter == word))]

def squelchMeaning(maxlensource):
    log.info("Preparing to squelch meanings")
    
    def inner(word):
        for reading, meaningfun in maxlensource[1](word):
            if meaningfun is None:
                yield reading, None
            else:
                def squelch(*meanargs):
                    meaning, measurewords = meaningfun(*meanargs)
                    return None, measurewords
                
                yield reading, squelch
    
    return maxlensource[0], inner

"""
Encapsulates one or more Chinese dictionaries, and provides the ability to transform
strings of Hanzi into their pinyin equivalents.
"""
class PinyinDictionary(object):
    # Regular expression used for pulling stuff out of the dictionary
    lineregex = re.compile(r"^([^#\s]+)\s+([^\s]+)\s+\[([^\]]+)\](\s+)?(.*)$")
    
    @classmethod
    def loadall(cls, dbconnect):
        def buildDictionary(usefallback, table, simptradindex):
            # DEBUG - this means that we will lose measure words for languages other than English - seperate the two
            rawsources = [
                    # User dictionary has absolute priority
                    fileSource('dict-userdict.txt'),
                    # Pinyin Toolkit specific overrides for system dictionaries
                    fileSource('pinyin_toolkit_sydict.u8'),
                    # Main language database
                    table and databaseDictionarySource(dbconnect, table, simptradindex) or None,
                    # Fallback databases for readings only if we have a non-english primary database
                    usefallback and squelchMeaning(databaseDictionarySource(dbconnect, "CEDICT", 1)) or None,
                    # Unihan as a last resort - lowest quality data
                    databaseReadingSource(dbconnect)
                ]
            
            return PinyinDictionary([source for source in rawsources if source is not None])
        
        dictionaries = {}
        for language, table, simptradindex in [('en', "CEDICT", 1), ('de', "HanDeDict", 0), ('fr', "CFDICT", 0), ('default', None, None)]:
            dictionaries[language] = Thunk(lambda l=language, t=table, sti=simptradindex: buildDictionary(l != 'en', t, sti))
        
        def inner(language):
            return (dictionaries.get(language, None) or dictionaries['default'])()
        
        return inner
    
    def __init__(self, maxlenssources):
        maxlens, self.__sources = unzip(maxlenssources)
        self.__maxcharacterlen = max(maxlens)

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
                while len(readingsmeanings) > 0 and readingsmeanings[0][1] is None:
                    readingsmeanings.pop(0)
                
                # Did we actually have a non-null meaning in there?
                if len(readingsmeanings) == 0:
                    # NB: we return None if there is no meaning in the codomain. This case can
                    # occur if the character only comes
                    log.info("We found a reading but no meaning for some text")
                    return None, None
                else:
                    # Instantiate the raw definition with our particular requirements
                    foundmeanings, foundmeasurewords = readingsmeanings[0][1](prefersimptrad, self.tonedchars)
                    
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
    # and be returned in priority order: highest priority first
    def parseexact(self, word):
        readingsmeanings = []
        for source in self.__sources:
            readingsmeanings.extend(source(word))
        
        # TODO: (perhaps) consolidate competing definitions from a single source if
        # they occur as a result of simplification and we prefer simplified characters
        
        # TODO: match up definitions /across/ sources so that we can get measure word
        # information in German (for example). (#120)
        
        return readingsmeanings

def combinemeaningsmws(dictmeanings, dictmeasurewords):
    if dictmeasurewords is not None and len(dictmeasurewords) > 0:
        return (dictmeanings or []) + [[Word(Text("MW: "))] + flattenmeasurewords(dictmeasurewords)]
    else:
        return dictmeanings

def flattenmeasurewords(dictmeasurewords):
    measurewordss = [charwords + [Word(Text(" - "))] + pinyinwords for (charwords, pinyinwords) in dictmeasurewords]
    return concat(intersperse([Word(Text(", "))], measurewordss))
