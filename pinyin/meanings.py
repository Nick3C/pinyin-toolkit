#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from logger import log
from pinyin import TokenList
import utils

class MeaningFormatter(object):
    embeddedchineseregex = re.compile(r"(?:(?:([^\|\[\s]*)\|([^\|\[\s]*))|([^\|\[\s]*))(?:\s*\[([^\]]*)\])?")
    
    def __init__(self, simplifiedcharindex, prefersimptrad):
        self.simplifiedcharindex = simplifiedcharindex
        self.prefersimptrad = prefersimptrad
    
    def parsedefinition(self, raw_definition, tonedchars_callback=None):
        log.info("Parsing the raw definition %s", raw_definition)
        
        meanings, measurewords = [], []
        for definition in raw_definition.strip().lstrip("/").rstrip("/").split("/"):
            # Remove spaces and replace all occurences of "CL:" with "MW:" as that is more meaningful
            definition = definition.strip().replace("CL:", "MW:")
            
            # Detect measure-word ness
            tokens = TokenList()
            if definition.startswith("MW:"):
                ismeasureword = True
                
                # Replace the commas with nicer ones that have spaces in
                definition = ", ".join(definition.lstrip("MW:").strip().split(","))
            else:
                ismeasureword = False
            
            for ismatch, thing in utils.regexparse(self.embeddedchineseregex, definition):
                if ismatch:
                    # A match - we can append a representation of the tokens it contains
                    self.formatmatch(tokens, thing, tonedchars_callback)
                else:
                    # Just a string: append it as-is
                    tokens.append(thing)
            
            # Add the tokens to the right pile
            if ismeasureword:
                measurewords.append(tokens)
            else:
                meanings.append(tokens)
            
        return meanings, measurewords
    
    def formatmatch(self, tokens, match, tonedchars_callback):
        if match.group(3) != None:
            # A single character standing by itself, with no | - just use the character
            character = match.group(3)
        elif self.prefersimptrad == "simp":
            # A choice of characters, and we want the simplified one
            character = match.group(1 + self.simplifiedcharindex)
        else:
            # A choice of characters, and we want the traditional one
            character = match.group(1 + (1 - self.simplifiedcharindex))
        
        if match.group(4) != None:
            # There was some pinyin for the character after it - include it
            tokens.append(character)
            tokens.append(" - ")
            tokens.appendspacedwordreading(TokenList.fromspacedstring(match.group(4)))
        else:
            if tonedchars_callback:
                # Look up the tone for the character so we can display it more nicely, as in the other branch
                tokens.extend(tonedchars_callback(character))
            else:
                # No callback, so the best we can do is to include the characters verbatim
                tokens.append(character)

if __name__=='__main__':
    import unittest
    
    class MeaningFormatterTest(unittest.TestCase):
        shangwu_def = u"/morning/CL:個|个[ge4]/"
        shangwu_meanings = [u"morning"]
        shangwu_simp_mws = [u"个 - ge4"]
        shangwu_trad_mws = [u"個 - ge4"]
        
        shu_def = u"/book/letter/same as 書經|书经 Book of History/CL:本[ben3],冊|册[ce4],部[bu4],叢|丛[cong2]/"
        shu_simp_meanings = [u"book", u"letter", u"same as 书经 Book of History"]
        shu_simp_mws = [u"本 - ben3, 册 - ce4, 部 - bu4, 丛 - cong2"]
        shu_trad_meanings = [u"book", u"letter", u"same as 書經 Book of History"]
        shu_trad_mws = [u"本 - ben3, 冊 - ce4, 部 - bu4, 叢 - cong2"]
        
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
            # 詞典 词典 [ci2 dian3] /dictionary (of Chinese compound words)/also written 辭典|辞典[ci2 dian3]/CL:部[bu4],本[ben3]/
            means, mws = self.parse(1, "simp", u"/dictionary (of Chinese compound words)/also written 辭典|辞典[ci2 dian3]/CL:部[bu4],本[ben3]/")
            self.assertEquals(means, [u"dictionary (of Chinese compound words)", u"also written 辞典 - ci2 dian3"])
            self.assertEquals(mws, [u"部 - bu4, 本 - ben3"])
    
        def testCallback(self):
            means, mws = self.parse(1, "simp", self.shu_def, tonedchars_callback=lambda x: ["JUNK"])
            self.assertEquals(means, [u'JUNK', u'JUNK', u'JUNKJUNK JUNKJUNK JUNKJUNK JUNKJUNK JUNKJUNK JUNK'])
    
        # Test helpers
        def parse(self, simplifiedcharindex, prefersimptrad, definition, tonedchars_callback=None):
            means, mws = MeaningFormatter(simplifiedcharindex, prefersimptrad).parsedefinition(definition, tonedchars_callback)
            return [mean.flatten() for mean in means], [mw.flatten() for mw in mws]
    
    unittest.main()