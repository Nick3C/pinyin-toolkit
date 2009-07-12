#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from logger import log
from pinyin import *
import utils

class MeaningFormatter(object):
    embeddedchineseregex = re.compile(r"(?:(?:([^\|\[\s]+)\|([^\|\[\s]+)(?:\s*\[([^\]]*)\])?)|(?:([^\|\[\s]+)\s*\[([^\]]*)\]))")
    
    def __init__(self, simplifiedcharindex, prefersimptrad):
        self.simplifiedcharindex = simplifiedcharindex
        self.prefersimptrad = prefersimptrad
    
    def parsedefinition(self, raw_definition, tonedchars_callback=None):
        log.info("Parsing the raw definition %s", raw_definition)
        
        # Default the toned characters callback to something sensible
        if tonedchars_callback is None:
            tonedchars_callback = lambda characters: [Word(Text(characters))]
        
        meanings, measurewords = [], []
        for definition in raw_definition.strip().lstrip("/").rstrip("/").split("/"):
            # Remove stray spaces
            definition = definition.strip()
            
            # Detect measure-word ness
            if definition.startswith("CL:"):
                ismeasureword = True
                
                # Measure words are comma-seperated
                for mw in definition[3:].strip().split(","):
                    # Attempt to parse the measure words as structured data
                    match = self.embeddedchineseregex.match(mw)
                    if match is None:
                        log.info("Could not parse the apparent measure word %s", mw)
                        continue
                    
                    # They SHOULD have pinyin information
                    characterswords, pinyinwords = self.formatmatch(match, tonedchars_callback)
                    if characterswords is None or pinyinwords is None:
                        log.info("The measure word %s was missing some information in the dictionary", mw)
                        continue
                    
                    measurewords.append((characterswords, pinyinwords))
            else:
                words = []
                for ismatch, thing in utils.regexparse(self.embeddedchineseregex, definition):
                    if ismatch:
                        # A match - we can append a representation of the words it contains
                        (characterwords, pinyinwords) = self.formatmatch(thing, tonedchars_callback)
                        
                        # Put the resulting words right into the output in a human-readable format
                        words.extend(characterwords)
                        if pinyinwords is not None:
                            words.append(Word(Text(" - ")))
                            words.extend(pinyinwords)
                    else:
                        # Just a string: append it as a list of tokens, trying to extract any otherwise-unmarked
                        # pinyin in the sentence for colorisation etc
                        words.append(Word(*tokenize(thing, forcenumeric=True)))
                
                meanings.append(words)
            
        return meanings, measurewords
    
    def formatmatch(self, match, tonedchars_callback):
        if match.group(4) != None:
            # A single character standing by itself, with no | - just use the character
            character = match.group(4)
        elif self.prefersimptrad == "simp":
            # A choice of characters, and we want the simplified one
            character = match.group(1 + self.simplifiedcharindex)
        else:
            # A choice of characters, and we want the traditional one
            character = match.group(1 + (1 - self.simplifiedcharindex))
        
        if match.group(4) != None:
            # Pinyin tokens (if any) will be present in single-character match case
            rawpinyin = match.group(5)
        else:
            # Pinyin tokens (if any) will be present in conjunctive character match case
            rawpinyin = match.group(3)
        
        if rawpinyin != None:
            # There was some pinyin for the character after it - include it
            pinyintokens = tokenizespaceseperated(rawpinyin)
            return ([Word(*(tonedcharactersfromreading(character, pinyintokens)))], [Word.spacedwordfromunspacedtokens(pinyintokens)])
        else:
            # Look up the tone for the character so we can display it more nicely, as in the other branch
            return (tonedchars_callback(character), None)

if __name__=='__main__':
    import unittest
    
    class MeaningFormatterTest(unittest.TestCase):
        shangwu_def = u"/morning/CL:個|个[ge4]/"
        shangwu_meanings = [u"morning"]
        shangwu_simp_mws = [(u'个', u'ge4')]
        shangwu_trad_mws = [(u'個', u'ge4')]
        
        shu_def = u"/book/letter/same as 書經|书经 Book of History/CL:本[ben3],冊|册[ce4],部[bu4],叢|丛[cong2]/"
        shu_simp_meanings = [u"book", u"letter", u"same as 书经 Book of History"]
        shu_simp_mws = [(u"本", u"ben3"), (u"册", "ce4"), (u"部", u"bu4"), (u"丛", "cong2")]
        shu_trad_meanings = [u"book", u"letter", u"same as 書經 Book of History"]
        shu_trad_mws = [(u"本", u"ben3"), (u"冊", u"ce4"), (u"部", u"bu4"), (u"叢", u"cong2")]
        
        def testDatesInMeaning(self):
            means, mws = self.parseunflat(1, "simp", u"/Jane Austen (1775-1817), English novelist/also written 简・奧斯汀|简・奥斯汀[Jian3 · Ao4 si1 ting1]/")
            self.assertEquals(len(means), 2)
            self.assertEquals(mws, [])
            
            self.assertEquals(flatten(means[0]), u"Jane Austen (1775-1817), English novelist")
            self.assertFalse(any([hasattr(token, "tone") for token in means[0]]))
        
        def testSplitNoMeasureWords(self):
            means, mws = self.parse(1, "simp", u"/morning/junk junk")
            self.assertEquals(means, [u"morning", u"junk junk"])
            self.assertEquals(mws, [])
        
        def testSplitMeasureWordsSimp(self):
            means, mws = self.parse(1, "simp", self.shangwu_def)
            self.assertEquals(means, self.shangwu_meanings)
            self.assertEquals(mws, self.shangwu_simp_mws)
        
        def testSplitMeasureWordsTrad(self):
            means, mws = self.parse(1, "trad", self.shangwu_def)
            self.assertEquals(means, self.shangwu_meanings)
            self.assertEquals(mws, self.shangwu_trad_mws)
        
        def testSplitSeveralMeasureWordsSimp(self):
            means, mws = self.parse(1, "simp", self.shu_def)
            self.assertEquals(means, self.shu_simp_meanings)
            self.assertEquals(mws, self.shu_simp_mws)
    
        def testSplitSeveralMeasureWordsTrad(self):
            means, mws = self.parse(1, "trad", self.shu_def)
            self.assertEquals(means, self.shu_trad_meanings)
            self.assertEquals(mws, self.shu_trad_mws)
    
        def testSplitSeveralMeasureWordsDifferentIndex(self):
            means, mws = self.parse(0, "simp", self.shu_def)
            self.assertEquals(means, self.shu_trad_meanings)
            self.assertEquals(mws, self.shu_trad_mws)
    
        def testSplitMultiEmbeddedPinyin(self):
            means, mws = self.parse(1, "simp", u"/dictionary (of Chinese compound words)/also written 辭典|辞典[ci2 dian3]/CL:部[bu4],本[ben3]/")
            self.assertEquals(means, [u"dictionary (of Chinese compound words)", u"also written 辞典 - ci2 dian3"])
            self.assertEquals(mws, [(u'部', 'bu4'), (u'本', u'ben3')])
    
        def testCallback(self):
            means, mws = self.parse(1, "simp", self.shu_def, tonedchars_callback=lambda x: Word(Text(u"JUNK")))
            self.assertEquals(means, [u'book', u'letter', u'same as JUNK Book of History'])
    
        def testColorsAttachedToBothHanziAndPinyin(self):
            means, mws = self.parseunflat(1, "simp", u"/sound of breaking or snapping (onomatopoeia)/also written 喀嚓|喀嚓 [ka1 cha1]/")
            self.assertEquals(flatten(means[0]), "sound of breaking or snapping (onomatopoeia)")
            self.assertEquals(means[1][-3], Word(TonedCharacter(u"喀", 1), TonedCharacter(u"嚓", 1)))
    
        def testColorsAttachedToHangingPinyin(self):
            means, mws = self.parseunflat(1, "simp", u"/silly hen3 definition hao3/a hen is not pinyin")
            self.assertEquals(means[0][0][2], Pinyin(u"hen", 3))
            self.assertEquals(means[0][0][-1], Pinyin(u"hao", 3))
            self.assertEquals(means[1][0][2], Text(u"hen"))
            
        # Test helpers
        def parse(self, *args, **kwargs):
            means, mws = self.parseunflat(*args, **kwargs)
            return [flatten(mean) for mean in means], [(flatten(mwcharwords), flatten(mwpinyinwords)) for (mwcharwords, mwpinyinwords) in mws]
        
        def parseunflat(self, simplifiedcharindex, prefersimptrad, definition, tonedchars_callback=None):
            return MeaningFormatter(simplifiedcharindex, prefersimptrad).parsedefinition(definition, tonedchars_callback=tonedchars_callback)
    
    unittest.main()