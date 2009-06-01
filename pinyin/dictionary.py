#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import re

from pinyin import *
import meanings
import utils

"""
Encapsulates one or more Chinese dictionaries, and provides the ability to transform
strings of Hanzi into their pinyin equivalents.
"""
class PinyinDictionary(object):
    # Regular expression used for pulling stuff out of the dictionary
    lineregex = re.compile(r"^([^#\s]+)\s+([^\s]+)\s+\[([^\]]+)\](\s+)?(.*)$")
    
    languagedicts = {
            'en'     : ('dict-cc-cedict.txt', 1),
            'de'     : ('dict-handedict.txt', 0),
            'fr'     : ('dict-cfdict.txt', 0),
            'pinyin' : ('dict-pinyin.txt', 1) # Not really a language, but handy for tests
        }
    
    @classmethod
    def load(cls, language, needmeanings=True):
        if not(needmeanings):
            # We can use the English dictionary if meanings are not required.  This is a good idea because it
            # has more pinyin than either of the other language dictionaries.
            (languagedict, simplifiedcharindex) = cls.languagedicts['en']
        else:
            # Default to the pinyin-only dictionary if this language doesn't have a dictionary.
            (languagedict, simplifiedcharindex) = cls.languagedicts.get(language, ('dict-pinyin.txt', 1))
        
        return PinyinDictionary([languagedict, 'dict-supplimentary.txt', 'dict-userdict.txt'], simplifiedcharindex, needmeanings)
    
    def __init__(self, dictnames, simplifiedcharindex, needmeanings):
        # Save the simplified index
        self.simplifiedcharindex = simplifiedcharindex
        
        # Build the actual dictionary, giving precedence to dictionaries later on in the input list
        self.__readings = {}
        self.__definition = {}
        for dictpath in [os.path.join(utils.executiondir(), dictname) for dictname in dictnames]:
            # Avoid loading dictionaries that aren't there (e.g. the dict-userdict.txt if the user hasn't created it)
            if os.path.exists(dictpath):
                self.loadsingledict(dictpath, needmeanings)
    
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
                
                # Find out the set of characters we should use as keys - if simplified and traditional coincide we can save space
                unique_characters = list(set([lcharacters, rcharacters]))
                
                # Parse readings
                for characters in unique_characters:
                    self.__readings[characters] = self.parsepinyin(raw_pinyin)
                
                # Parse meanings
                if needmeanings:
                    meanings = m.group(5)
                    if meanings:
                        for characters in unique_characters:
                            # We just save the raw meaning into the dictionary, so we don't clean up meanings we never look at
                            self.__definition[characters] = meanings
        finally:
            file.close()

    def parsepinyin(self, raw_pinyin):
        # Read the pinyin into the array: sometimes this field contains
        # english (e.g. in the pinyin for 'T shirt') so we better handle that
        tokens = TokenList()
        for the_raw_pinyin in raw_pinyin.split():
            try:
                tokens.append(Pinyin(the_raw_pinyin))
            except ValueError:
                tokens.append(the_raw_pinyin)
        
        # Special treatment for the erhua suffix: never show the tone in the string representation.
        # NB: currently hideneutraltone defaults to True, so this is sort of pointless.
        last_token = tokens[-1]
        if utils.iserhuapinyintoken(last_token):
            last_token.hideneutraltone = True
        
        return tokens

    """
    Given a string of Hanzi, return the result rendered into a list of Pinyin and unrecognised tokens (as strings).
    """
    def reading(self, sentence):
        def addword(tokens, thing):
            # If we already have some text building up, add a preceding space.
            # However, if the word we got looks like punctuation, don't do it.
            # This ensures consistency in the treatment of Western and Chinese
            # punctuation.  Furthermore, avoid adding double-spaces.  This is
            # also important for punctuation consistency, because Western
            # punctuation is typically followed by a space whereas the Chinese
            # equivalents are not.
            have_some_text = len(tokens) > 0
            is_punctuation = utils.ispunctuation(thing)
            already_have_space = have_some_text and tokens[-1].endswith(u' ')
            if have_some_text and not(is_punctuation) and not(already_have_space):
                tokens.append(u' ')
            
            # Add the tokens to the tokens, with spaces between the components
            reading_tokens = self.__readings[thing]
            reading_tokens_count = len(reading_tokens)
            for n, reading_token in enumerate(reading_tokens):
                # Don't add spaces if this is the first token or if we are at the
                # last token and have an erhua
                if n != 0 and (n != reading_tokens_count - 1 or not(utils.iserhuapinyintoken(reading_token))):
                    tokens.append(u' ')
                
                tokens.append(reading_token)
        
        return self.mapparsedtokens(sentence, addword)

    """
    Given a string of Hanzi, return the result rendered into a list of characters with tone information and unrecognised tokens (as string).
    """
    def tonedchars(self, sentence):
        def addword(tokens, thing):
            # Add characters to the tokens /without/ spaces between them, but with tone info
            for character, reading_token in zip(thing, self.__readings[thing]):
                if hasattr(reading_token, "tone"):
                    tokens.append(TonedCharacter(character, reading_token.tone))
                else:
                    # Sometimes the tokens do not have tones (e.g. in the translation for T-shirt)
                    tokens.append(character)
        
        return self.mapparsedtokens(sentence, addword)

    def mapparsedtokens(self, sentence, addword):
        # Represents the resulting token stream
        tokens = TokenList()
        
        for recognised, thing in self.parse(sentence):
            if not recognised:
                # A single unrecognised character: it's probably just whitespace or punctuation.
                # Append it directly to the token list.
                tokens.append(thing)
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
        foundmeanings, foundmeasurewords = None, None
        for recognised, word in self.parse(sentence):
            if recognised:
                # A recognised thing! Did we recognise something else already?
                if foundmeanings != None or foundmeasurewords != None:
                    # This is a phrase with more than one word - let someone else translate it
                    return None, None
                
                # Find the definition in the dictionary
                definition = self.__definition.get(word)
                if definition == None:
                    # NB: we return None if there is no meaning in the codomain. This case can
                    # occur if the dictionary was built with needmeanings=False
                    return None, None
                else:
                    # We got a raw definition, but we need to clean up it before using it
                    foundmeanings, foundmeasurewords = meanings.MeaningFormatter(self.simplifiedcharindex, prefersimptrad).parsedefinition(definition, self.tonedchars)

        return foundmeanings, foundmeasurewords

    """
    Return meanings and measure words for the sentence, if available.
    """
    def flatmeanings(self, sentence, prefersimptrad):
        dictmeanings, dictmeasurewords = self.meanings(sentence, prefersimptrad)
        
        if dictmeanings != None or dictmeasurewords != None:
            return (dictmeanings or []) + [TokenList(["MW: "] + dictmeasureword) for dictmeasureword in (dictmeasurewords or [])]
        else:
            return None

    def parse(self, sentence):
        assert type(sentence)==unicode
        if sentence == None or len(sentence) == 0:
            return
        
        # Strip HTML
        sentence = re.sub('<(?!(?:a\s|/a|!))[^>]*>', '', sentence)
        
        
        # DEBUG - New unfinished code to hunt for matches from largest to smallest in efficient way
        """
        # Use a two loop structure to hunt for words, starting with longest word and then checking for smaller units:
        
        #  1 2 3 4
        #a _ _ _ _   Start with the longest word
        #  _ _ _     Reduce Length and loop again
        #  _ _ _     
        #b _ _       Reduce Length again and do small loop
        #    _ _
        #      _ _
        #c _
        #    _
        #      _
        #        _
        
        # once second loop has finished we may have found something in eg sentence[1:2]
        # if so then we should skip the found word and start from the end of the first word

        #function that deals does a lookup and returns the result as a list [True/False,startpos/None,length/None]
        def checkisword(candidate_word,i,startpos,length):
            if self.__readings.has_key(candidate_word) :
                # The candidate word was found in the dictionary. Yay!
                return True,startpos,length
                largest_word = candidate_word
            elif len(candidate_word) == 1:
                # If it's a single character and not found,
                # then we'll just give back the original character itself.
                yield (False, candidate_word)
                # Look for new words, starting from just after this character
            else:
                # This word isn't in the dictionary.
                # It's POSSIBLE that it will be in there if we kept looking,
                # but for now let's just assume this is the end

        
        # Set defalts      
        isphrase=False                       # assume not a phrase
        senlen=len(sentence)
        checklen=senlen                       # start with whole phrase as check
        foundwords=[]
        foundwords[0]=[]
        
        while checklen > 0:                   # create a big loop that wil iterate the size of the word being checked
            startpos=0
            while startpos < endpos:          # create a small loop that starts at the first charecter and hunts for words of this length
                checkword(sentenced[startpos:endpos])
                endpos=startpos+checklength    # 
                startpost+=1                   # add one to the start position and iterate the small loop

            checklen-=1                        # decrease the check length by 1 and iterate the big loop
 
                foundwordstartpos[i]=startpos
                foundwordendpos[i]=

                    
        """

        
        
        
        # Iterate through the text
        i = 0;
        while i < len(sentence):
            largest_word = None
            
            # Look for progressively bigger multi-syllabic chinese words
            j = i + 1
            while j <= len(sentence) :
                candidate_word = sentence[i:j]
                if self.__readings.has_key(candidate_word) :
                    # The candidate word looked like a real one -
                    # record it as the largest word so far
                    largest_word = candidate_word
                    # try again with a bigger word
                    j += 1
                elif len(candidate_word) == 1:
                    # If it's a single character and not found,
                    # then we'll just give back the original character itself.
                    yield (False, candidate_word)
                    # Look for new words, starting from just after this character
                    break
                else:
                    # A multiple-character word that isn't in the dictionary.
                    # It's POSSIBLE that it will be in there if we kept looking,
                    # but for now let's just assume this is the end
                    break
            
            if largest_word == None:
                # If the largest_word is empty, then either we didn't find a word
                # in front at all, OR we just added it to the reading.  In either case,
                # we should start the search again strictly after the current character
                i = j
            else:
                # Find the tokens recorded in the dictionary for this word and yield them
                yield (True, largest_word)
                                
                # Continue looking for new words after the end of this one
                i += len(largest_word)


# Testsuite
if __name__=='__main__':
    import unittest
    
    # Preload commonly-used dictionaries to prevent reading them several times
    pinyindict = PinyinDictionary.load('pinyin', True)
    englishdict = PinyinDictionary.load('en', True)
            
    class TestPinyinDictionary(unittest.TestCase):
        def testTonedTokens(self):
            toned = pinyindict.tonedchars(u"一个")
            self.assertEquals(toned.flatten(), u"一个")
            self.assertEquals(toned[0].tone, 1)
            self.assertEquals(toned[1].tone, 4)

        def testTonedTokensWithoutTone(self):
            toned = pinyindict.tonedchars(u"T恤")
            self.assertEquals(toned.flatten(), u"T恤")
            self.assertEquals(toned[1].tone, 4)

        def testPhraseMeanings(self):
            self.assertEquals(self.flatmeanings(englishdict, u"一杯啤酒"), None)

        def testMeaningsWithTrailingJunk(self):
            self.assertEquals(self.flatmeanings(englishdict, u"鼓聲 (junk!!)"), ["sound of a drum", "drumbeat"])
        
        def testMeaningless(self):
            self.assertEquals(self.flatmeanings(englishdict, u"English"), None)

        def testMissingDictionary(self):
            dict = PinyinDictionary(['idontexist.txt'], 1, True)
            self.assertEquals(dict.reading(u"个").flatten(), u"个")
            self.assertEquals(self.flatmeanings(dict, u"个"), None)
        
        def testMissingLanguage(self):
            dict = PinyinDictionary.load('foobar', True)
            self.assertEquals(dict.reading(u"个").flatten(), "ge4")
            self.assertEquals(self.flatmeanings(dict, u"个"), None)
        
        def testPinyinDictionary(self):
            self.assertEquals(pinyindict.reading(u"一个").flatten(), "yi1 ge4")
            self.assertEquals(pinyindict.reading(u"一個").flatten(), "yi1 ge4")
            self.assertEquals(self.flatmeanings(pinyindict, u"一个"), None)
        
        def testGermanDictionary(self):
            dict = PinyinDictionary.load('de', True)
            self.assertEquals(dict.reading(u"请").flatten(), "qing3")
            self.assertEquals(dict.reading(u"請").flatten(), "qing3")
            self.assertEquals(self.flatmeanings(dict, u"請"), ["Bitte ! (u.E.) (Int)", "bitten, einladen (u.E.) (V)"])
    
        def testEnglishDictionary(self):
            self.assertEquals(englishdict.reading(u"鼓聲").flatten(), "gu3 sheng1")
            self.assertEquals(englishdict.reading(u"鼓声").flatten(), "gu3 sheng1")
            self.assertEquals(self.flatmeanings(englishdict, u"鼓聲"), ["sound of a drum", "drumbeat"])
    
        def testFrenchDictionary(self):
            dict = PinyinDictionary.load('fr', True)
            self.assertEquals(dict.reading(u"白天").flatten(), "bai2 tian")
            self.assertEquals(dict.reading(u"白天").flatten(), "bai2 tian")
            self.assertEquals(self.flatmeanings(dict, u"白天"), [u"journée (n.v.) (n)"])
    
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
        
        def flattenall(self, things):
            return [thing.flatten() for thing in things]
    
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
            return pinyindict.reading(what).flatten()
    
    unittest.main()
