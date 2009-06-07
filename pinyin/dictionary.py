#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import re

from logger import log
from pinyin import *
import meanings
from utils import *
import weakcache


"""
Encapsulates one or more Chinese dictionaries, and provides the ability to transform
strings of Hanzi into their pinyin equivalents.
"""
class PinyinDictionary(object):
    languagedicts = {
            'en'     : ('cedict_ts.u8', 1),
            'de'     : ('handedict_nb.u8', 0),
            'fr'     : ('cfdict_nb.u8', 0),
            'pinyin' : ('cedict_pinyin.u8', 1) # Not really a language, but handy for tests
        }
    
    # A cache of dictionaries loaded by the program, trimmed when we run low on memory
    dictionarycache = weakcache.WeakCache(lambda (language, needmeanings): PinyinDictionary.uncachedload(language, needmeanings))

    # Regular expression used for pulling stuff out of the dictionary
    lineregex = re.compile(r"^([^#\s]+)\s+([^\s]+)\s+\[([^\]]+)\](\s+)?(.*)$")
    
    @classmethod
    def load(cls, language, needmeanings=True):
        return cls.dictionarycache[(language, needmeanings)]
    
    @classmethod
    def uncachedload(cls, language, needmeanings):
        if not(needmeanings):
            # We can use the English dictionary if meanings are not required.  This is a good idea because it
            # has more pinyin than either of the other language dictionaries.
            (languagedict, simplifiedcharindex) = cls.languagedicts['en']
        else:
            # Default to the pinyin-only dictionary if this language doesn't have a dictionary.
            # DEBUG - this means that we will lose measure words for languages other than English - seperate the two
            (languagedict, simplifiedcharindex) = cls.languagedicts.get(language, ('cedict_pinyin.u8', 1))
        
        log.info("Beginning load of dictionary for language code %s (%s), need meanings = %s", language, languagedict, needmeanings)
        return PinyinDictionary([languagedict, 'pinyin_toolkit_sydict.u8', 'dict-userdict.txt'], simplifiedcharindex, needmeanings)
    
    def __init__(self, dictnames, simplifiedcharindex, needmeanings):
        # Save the simplified index
        self.__simplifiedcharindex = simplifiedcharindex
        
        # Build the actual dictionary, giving precedence to dictionaries later on in the input list
        self.__maxcharacterlen = 0
        self.__readings = {}
        self.__definition = {}
        for dictpath in [os.path.join(pinyindir(), "dictionaries", dictname) for dictname in dictnames]:
            # Avoid loading dictionaries that aren't there (e.g. the dict-userdict.txt if the user hasn't created it)
            if os.path.exists(dictpath):
                log.info("Loading dictionary from %s, load meanings = %s", dictpath, needmeanings)
                self.loadsingledict(dictpath, needmeanings)
            else:
                log.warn("Skipping missing dictionary at %s", dictpath)
    
    def loadsingledict(self, dictpath, needmeanings):
        file = codecs.open(dictpath, "r", encoding='utf-8')
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
                
                # Parse readings
                pinyin = TokenList.fromspacedstring(raw_pinyin)
                
                # Save meanings and readings
                for characters in [lcharacters, rcharacters]:
                    # Update the maximum character length
                    self.__maxcharacterlen = max(self.__maxcharacterlen, len(characters))
                    
                    # Always save the readings
                    self.__readings[characters] = pinyin
                    
                    if needmeanings and raw_definition:
                        # We just save the raw definition into the dictionary, so we don't clean up meanings we never look at
                        self.__definition[characters] = raw_definition
        finally:
            file.close()

    """
    Given a string of Hanzi, return the result rendered into a list of Pinyin and unrecognised tokens (as strings).
    """
    def reading(self, sentence):
        log.info("Requested reading for %s", sentence)
        
        def addword(tokens, thing):
            # If we already have some text building up, add a preceding space.
            # However, if the word we got looks like punctuation, don't do it.
            # This ensures consistency in the treatment of Western and Chinese
            # punctuation.  Furthermore, avoid adding double-spaces.  This is
            # also important for punctuation consistency, because Western
            # punctuation is typically followed by a space whereas the Chinese
            # equivalents are not.
            have_some_text = len(tokens) > 0
            is_punctuation = ispunctuation(thing)
            already_have_space = have_some_text and tokens[-1].endswith(u' ')
            if have_some_text and not(is_punctuation) and not(already_have_space):
                tokens.append(Text(u' '))
            
            # Add this reading into the token list with nice formatting
            tokens.append(Word.spacedwordreading(self.__readings[thing]))
        
        return self.mapparsedtokens(sentence, addword)

    """
    Given a string of Hanzi, return the result rendered into a list of characters with tone information and unrecognised tokens (as string).
    """
    def tonedchars(self, sentence):
        log.info("Requested toned characters for %s", sentence)
        
        def addword(tokens, thing):
            reading_tokens = self.__readings[thing]
            
            # If we can't associate characters with tokens on a one-to-one basis we had better give up
            if len(thing) != len(reading_tokens):
                log.warn("Couldn't produce toned characters for %s because there are a different number of reading tokens than characters", thing)
                tokens.append(Text(thing))
                return
            
            # Add characters to the tokens /without/ spaces between them, but with tone info
            wordtokens = TokenList([])
            for character, reading_token in zip(thing, reading_tokens):
                # Avoid making the numbers from the supplementary dictionary into toned
                # things, because it confuses users :-)
                if hasattr(reading_token, "tone") and not(character.isdecimal()):
                    wordtokens.append(TonedCharacter(character, reading_token.tone))
                else:
                    # Sometimes the tokens do not have tones (e.g. in the translation for T-shirt)
                    wordtokens.append(Text(character))
            
            tokens.append(Word(wordtokens))
        
        return self.mapparsedtokens(sentence, addword)

    def mapparsedtokens(self, sentence, addword):
        # Represents the resulting token stream
        tokens = TokenList()
        
        for recognised, thing in self.parse(sentence):
            if not recognised:
                # A single unrecognised character: it's probably just whitespace or punctuation.
                # Append it directly to the token list.
                tokens.append(Text(thing))
            else:
                # Got a recognised token sequence! Hooray! Use the user-supplied function to add this
                # thing to the output
                addword(tokens, thing)
        
        return tokens

    """
    Given a string of Hanzi, return definitions and measure words for the first recognisable thing in the string.
    If there is more than one recognisable thing then assume it is a phrase and don't return a meaning.
    """
    def meanings(self, sentence, prefersimptrad):
        log.info("Requested meanings for %s", sentence)
        
        foundmeanings, foundmeasurewords = None, None
        for recognised, word in self.parse(sentence):
            if recognised:
                # A recognised thing! Did we recognise something else already?
                if foundmeanings != None or foundmeasurewords != None:
                    # This is a phrase with more than one word - let someone else translate it
                    log.info("We found a phrase, so returning no meanings")
                    return None, None
                
                # Find the definition in the dictionary
                definition = self.__definition.get(word)
                if definition == None:
                    # NB: we return None if there is no meaning in the codomain. This case can
                    # occur if the dictionary was built with needmeanings=False
                    log.info("We appear to have loaded a dictionary with no meanings, so returning early")
                    return None, None
                else:
                    # We got a raw definition, but we need to clean up it before using it
                    foundmeanings, foundmeasurewords = meanings.MeaningFormatter(self.__simplifiedcharindex, prefersimptrad).parsedefinition(definition, self.tonedchars)                  

        return foundmeanings, foundmeasurewords

    """
    Return meanings and measure words for the sentence, if available.
    """
    def flatmeanings(self, sentence, prefersimptrad):
        dictmeanings, dictmeasurewords = self.meanings(sentence, prefersimptrad)
        
        if dictmeanings != None or dictmeasurewords != None:
            return (dictmeanings or []) + [TokenList([Text("MW: ")] + dictmeasureword) for dictmeasureword in (dictmeasurewords or [])]
        else:
            return None

    def parse(self, sentence):
        assert type(sentence)==unicode
        if sentence == None or len(sentence) == 0:
            return
        
        # Strip HTML
        sentence = re.sub('<(?!(?:a\s|/a|!))[^>]*>', '', sentence)
        
        # Iterate through the text
        i = 0;
        while i < len(sentence):
            # Try all possible word lengths (naive, but easy to code)
            found_something = False
            for word_len in range(self.__maxcharacterlen, 0, -1):
                candidate_word = sentence[i:i + word_len]
                if self.__readings.has_key(candidate_word) :
                    # A real word! Let's yield it immediately
                    yield (True, candidate_word)
                    
                    # Continue looking for a new word after the end of this one
                    found_something = True
                    i += word_len
                    break
            
            if not(found_something):
                # Failed to find a single valid word in this text, so let's just yield
                # a single character token. TODO: yield multi-character tokens for efficiency.
                yield (False, sentence[i:i+1])
                i += 1


# Testsuite
if __name__=='__main__':
    import unittest
    
    # Thunk commonly-used dictionaries to prevent reading them several times
    pinyindict = Thunk(lambda: PinyinDictionary.load('pinyin', True))
    englishdict = Thunk(lambda: PinyinDictionary.load('en', True))
    germandict = Thunk(lambda: PinyinDictionary.load('de', True))
    
    class TestPinyinDictionary(unittest.TestCase):
        def testTonedTokens(self):
            toned = pinyindict.tonedchars(u"一个")
            self.assertEquals(flatten(toned), u"一个")
            self.assertEquals(toned[0].token[0].tone, 1)
            self.assertEquals(toned[0].token[1].tone, 4)

        def testTonedTokensWithoutTone(self):
            toned = pinyindict.tonedchars(u"T恤")
            self.assertEquals(flatten(toned), u"T恤")
            self.assertEquals(toned[0].token[1].tone, 4)

        def testTonedTokenNumbers(self):
            # Although it kind of makes sense to return the arabic numbers with tone colors, users don't expect it :-)
            toned = pinyindict.tonedchars(u"1994")
            self.assertEquals(flatten(toned), u"1994")
            self.assertEquals([hasattr(token, "tone") for token in toned], [False, False])

        def testNumbersWherePinyinLengthDoesntMatchCharacters(self):
            self.assertEquals(flatten(englishdict.tonedchars(u"1000000000")), u"1000000000")
            self.assertEquals(flatten(englishdict.reading(u"1000000000")), u"yi1 shi2 yi4")
            self.assertEquals(self.flatmeanings(englishdict, u"1000000000"), None)

        def testPhraseMeanings(self):
            self.assertEquals(self.flatmeanings(englishdict, u"一杯啤酒"), None)

        def testMeaningsWithTrailingJunk(self):
            self.assertEquals(self.flatmeanings(englishdict, u"鼓聲 (junk!!)"), ["sound of a drum", "drumbeat"])
        
        def testMeaningless(self):
            self.assertEquals(self.flatmeanings(englishdict, u"English"), None)

        def testMissingDictionary(self):
            dict = PinyinDictionary(['idontexist.txt'], 1, True)
            self.assertEquals(flatten(dict.reading(u"个")), u"个")
            self.assertEquals(self.flatmeanings(dict, u"个"), None)
        
        def testMissingLanguage(self):
            dict = PinyinDictionary.load('foobar', True)
            self.assertEquals(flatten(dict.reading(u"个")), "ge4")
            self.assertEquals(self.flatmeanings(dict, u"个"), None)
        
        def testPinyinDictionary(self):
            self.assertEquals(flatten(pinyindict.reading(u"一个")), "yi1 ge4")
            self.assertEquals(flatten(pinyindict.reading(u"一個")), "yi1 ge4")
            self.assertEquals(self.flatmeanings(pinyindict, u"一个"), None)
        
        def testGermanDictionary(self):
            self.assertEquals(flatten(germandict.reading(u"请")), "qing3")
            self.assertEquals(flatten(germandict.reading(u"請")), "qing3")
            self.assertEquals(self.flatmeanings(germandict, u"請"), ["Bitte ! (u.E.) (Int)", "bitten, einladen (u.E.) (V)"])
    
        def testEnglishDictionary(self):
            self.assertEquals(flatten(englishdict.reading(u"鼓聲")), "gu3 sheng1")
            self.assertEquals(flatten(englishdict.reading(u"鼓声")), "gu3 sheng1")
            self.assertEquals(self.flatmeanings(englishdict, u"鼓聲"), ["sound of a drum", "drumbeat"])
    
        def testFrenchDictionary(self):
            dict = PinyinDictionary.load('fr', True)
            self.assertEquals(flatten(dict.reading(u"白天")), "bai2 tian")
            self.assertEquals(flatten(dict.reading(u"白天")), "bai2 tian")
            self.assertEquals(self.flatmeanings(dict, u"白天"), [u"journée (n.v.) (n)"])
    
        def testWordsWhosePrefixIsNotInDictionary(self):
            self.assertEquals(flatten(germandict.reading(u"生日")), "sheng1 ri4")
            self.assertEquals(self.flatmeanings(germandict, u"生日"), [u"Geburtstag (S)"])
    
        def testProperName(self):
            self.assertEquals(flatten(englishdict.reading(u"珍・奥斯汀")), u"Zhen1 · Ao4 si1 ting1")
            self.assertEquals(self.flatmeanings(englishdict, u"珍・奥斯汀"), [u"Jane Austen (1775-1817), English novelist", u"also written 简・奥斯汀 - Jian3 · Ao4 si1 ting1"])
    
        def testShortPinyin(self):
            self.assertEquals(flatten(englishdict.reading(u"股指")), "gu3 zhi3")
            self.assertEquals(self.flatmeanings(englishdict, u"股指"), [u"stock market index", u"share price index", u"abbr. for 股票指数 - gu3 piao4 zhi3 shu4"])
    
        def testSimpMeanings(self):
            self.assertEquals(self.flatmeanings(englishdict, u"书", prefersimptrad="simp"), [u"book", u"letter", u"same as 书经 Book of History", u"MW: 本 - ben3, 册 - ce4, 部 - bu4, 丛 - cong2"])
        
        def testTradMeanings(self):
            self.assertEquals(self.flatmeanings(englishdict, u"书", prefersimptrad="trad"), [u"book", u"letter", u"same as 書經 Book of History", u"MW: 本 - ben3, 冊 - ce4, 部 - bu4, 叢 - cong2"])
        
        def testNonFlatMeanings(self):
            dictmeanings, dictmeasurewords = englishdict.meanings(u"书", prefersimptrad="simp")
            self.assertEquals(self.flattenall(dictmeanings), [u"book", u"letter", u"same as 书经 Book of History"])
            self.assertEquals(self.flattenall(dictmeasurewords), [u"本 - ben3, 册 - ce4, 部 - bu4, 丛 - cong2"])
        
        # Test helper 
        def flatmeanings(self, dictionary, what, prefersimptrad="simp"):
            dictmeanings = dictionary.flatmeanings(what, prefersimptrad)
            if dictmeanings:
                return self.flattenall(dictmeanings)
            else:
                return None
        
        def flattenall(self, tokens):
            return [flatten(token) for token in tokens]
    
    class TestPinyinConverter(unittest.TestCase):
        # Test data:
        nihao_simp = u'你好，我喜欢学习汉语。我的汉语水平很低。'
        nihao_trad = u'你好，我喜歡學習漢語。我的漢語水平很低。'
        nihao_simp_western_punc = u'你好, 我喜欢学习汉语. 我的汉语水平很低.'
        nihao_reading = u"ni3 hao3, wo3 xi3 huan xue2 xi2 Han4 yu3. wo3 de Han4 yu3 shui3 ping2 hen3 di1."
    
        def testSimplifiedPinyin(self):
            self.assertEqual(self.reading(self.nihao_simp), self.nihao_reading)
    
        def testTraditionalPinyin(self):
            self.assertEqual(self.reading(self.nihao_trad), self.nihao_reading)
    
        def testWesternPunctuation(self):
            self.assertEqual(self.reading(self.nihao_simp_western_punc), self.nihao_reading)
    
        def testEmptyString(self):
            self.assertEqual(self.reading(u""), u"")
    
        def testMixedEnglishChinese(self):
            self.assertEqual(self.reading(u"你 (pr.)"), u"ni3 (pr.)")
    
        def testNeutralRSuffix(self):
            self.assertEqual(self.reading(u"一塊兒"), "yi1 kuai4r")
    
        # Test helpers
        def reading(self, what):
            return flatten(pinyindict.reading(what))
    
    unittest.main()
