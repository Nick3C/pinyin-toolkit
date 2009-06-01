#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

import utils

class MeaningFormatter(object):
    mwregex = re.compile(r"(?:(?:([^\|\[]*)\|([^\|\[]*))|([^\|\[]*))(?:\s*\[(.*)\])?")
    
    def __init__(self, detectmeasurewords, simplifiedcharindex, prefersimptrad):
        self.detectmeasurewords = detectmeasurewords
        self.simplifiedcharindex = simplifiedcharindex
        self.prefersimptrad = prefersimptrad
    
    def splitmeanings(self, dictmeanings):
        # If we didn't get any information from the dictionary, just give up
        if dictmeanings == None:
            return None, None
        
        # Replace all occurences of "CL:" with "MW:" as that is more meaningful
        dictmeanings = [dictmeaning.replace("CL:", "MW:") for dictmeaning in dictmeanings]
        
        if not(self.detectmeasurewords):
            # Return any measure words as part of the list of meanings
            onlymeanings, measurewords = dictmeanings, None
        else:
            # OK, we're looking for measure words - scan each meaning looking for some
            onlymeanings, measurewords = [], []
            for dictmeaning in dictmeanings:
                measureword = self.parsemeasureword(dictmeaning)
                if measureword != None:
                    # It's a measure word - append to measure word list
                    measurewords.append(measureword)
                else:
                    # Not a measure word, so it must be a plain meaning
                    onlymeanings.append(dictmeaning)
        
        return onlymeanings, measurewords
    
    # Allows us to detect measure word data from dictionary
    # Currently only English CC-CEDICT support this function
    def parsemeasureword(self, meaning):
        # TODO: this routine is somewhat broken
        if meaning.startswith("MW:"):
            finalmeasurewords = []
            for measureword in meaning.lstrip("MW:").split(","):
                match = self.mwregex.match(measureword)
                
                if match == None and not(utils.isdebugmode()):
                    # If the regex failed to match, fail gracefully
                    finalmeasurewords.append(measureword)
                    continue
                
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
                    # TODO: output it as a pinyin token?
                    finalmeasurewords.append(character + " - " + match.group(4))
                else:
                    # There was no pinyin for the character - just include it
                    finalmeasurewords.append(character)
        
            # TODO: Nick wants to do something with audio here?
            # " [sound:MW]" # DEBUG - pass to audio loop
            return ", ".join(finalmeasurewords)
        else:
            return None

if __name__=='__main__':
    import unittest
    
    class MeaningFormatterTest(unittest.TestCase):
        shangwu_meanings = [u"morning", u"CL:個|个[ge4]"]
        shu_meanings = [u"book", u"letter", u"same as 書經|书经 Book of History", u"CL:本[ben3],冊|册[ce4],部[bu4],叢|丛[cong2]"]
        
        def testSplitNoMeanings(self):
            means, mws = MeaningFormatter(True, 1, "simp").splitmeanings(None)
            self.assertEquals(means, None)
            self.assertEquals(mws, None)
        
        def testSplitNoMeasureWords(self):
            means, mws = MeaningFormatter(True, 1, "simp").splitmeanings([u"morning", u"junk junk"])
            self.assertEquals(means, [u"morning", u"junk junk"])
            self.assertEquals(mws, [])
        
        def testSplitMeasureWordsOff(self):
            means, mws = MeaningFormatter(False, 1, "simp").splitmeanings(self.shangwu_meanings)
            self.assertEquals(means, ["morning", u"MW:個|个[ge4]"])
            self.assertEquals(mws, None)
    
        def testSplitMeasureWordsSimp(self):
            means, mws = MeaningFormatter(True, 1, "simp").splitmeanings(self.shangwu_meanings)
            self.assertEquals(means, ["morning"])
            self.assertEquals(mws, [u"个 - ge4"])
        
        def testSplitMeasureWordsTrad(self):
            means, mws = MeaningFormatter(True, 1, "trad").splitmeanings(self.shangwu_meanings)
            self.assertEquals(means, ["morning"])
            self.assertEquals(mws, [u"個 - ge4"])
        
        def testSplitSeveralMeasureWordsSimp(self):
            means, mws = MeaningFormatter(True, 1, "simp").splitmeanings(self.shu_meanings)
            self.assertEquals(means, [u"book", u"letter", u"same as 書經|书经 Book of History"])
            self.assertEquals(mws, [u"本 - ben3, 册 - ce4, 部 - bu4, 丛 - cong2"])
    
        def testSplitSeveralMeasureWordsTrad(self):
            means, mws = MeaningFormatter(True, 1, "trad").splitmeanings(self.shu_meanings)
            self.assertEquals(means, [u"book", u"letter", u"same as 書經|书经 Book of History"])
            self.assertEquals(mws, [u"本 - ben3, 冊 - ce4, 部 - bu4, 叢 - cong2"])
    
        def testSplitSeveralMeasureWordsDifferentIndex(self):
            means, mws = MeaningFormatter(True, 0, "simp").splitmeanings(self.shu_meanings)
            self.assertEquals(means, [u"book", u"letter", u"same as 書經|书经 Book of History"])
            self.assertEquals(mws, [u"本 - ben3, 冊 - ce4, 部 - bu4, 叢 - cong2"])
    
    unittest.main()