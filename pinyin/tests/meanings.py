# -*- coding: utf-8 -*-

import unittest

from pinyin.meanings import *


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
