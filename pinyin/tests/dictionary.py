# -*- coding: utf-8 -*-

import unittest

from pinyin.dictionary import *
from database import *


dictionaries = PinyinDictionary.loadall(database)
englishdict, frenchdict, germandict = dictionaries('en'), dictionaries('fr'), dictionaries('de')

class PinyinDictionaryTest(unittest.TestCase):
    def testTonedTokens(self):
        toned = englishdict.tonedchars(u"一个")
        self.assertEquals(flatten(toned), u"一个")
        self.assertEquals(toned[0][0].toneinfo, ToneInfo(written=1))
        self.assertEquals(toned[0][1].toneinfo, ToneInfo(written=4))
    
    def testTonedCharactersPreservesWhitespace(self):
        self.assertEquals(flatten(englishdict.tonedchars(u"\t一个")), u"\t一个")

    def testTonedTokensWithoutTone(self):
        toned = englishdict.tonedchars(u"T恤")
        self.assertEquals(flatten(toned), u"T恤")
        self.assertEquals(toned[0][1].toneinfo, ToneInfo(written=4))

    def testTonedTokenNumbers(self):
        # Although it kind of makes sense to return the arabic numbers with tone colors, users don't expect it :-)
        toned = englishdict.tonedchars(u"1994")
        self.assertEquals(flatten(toned), u"1994")
        self.assertFalse(any([hasattr(token, "tone") for token in toned]))

    def testNumbersWherePinyinLengthDoesntMatchCharacters(self):
        self.assertEquals(flatten(englishdict.tonedchars(u"1000000000")), u"1000000000")
        # Invalidated by removal of numbers from the dictionary:
        # self.assertEquals(flatten(englishdict.reading(u"1000000000")), u"yi1 shi2 yi4")
        self.assertEquals(self.flatmeanings(englishdict, u"1000000000"), None)

    def testPhraseMeanings(self):
        self.assertEquals(self.flatmeanings(englishdict, u"一杯啤酒"), None)
        self.assertEquals(self.flatmeanings(englishdict, u"U盘"), None)
    
    def testPhraseMeaningsNotFoundBecauseOfWhitespacePunctuation(self):
        self.assertNotEquals(self.flatmeanings(englishdict, u"你好!"), None)
        self.assertNotEquals(self.flatmeanings(englishdict, u"你好!!!"), None)
        self.assertNotEquals(self.flatmeanings(englishdict, u"  你好  "), None)

    # Invalidated by fix to issue #71
    # def testMeaningsWithTrailingJunk(self):
    #             self.assertEquals(self.flatmeanings(englishdict, u"鼓聲 (junk!!)"), ["sound of a drum", "drumbeat"])
    
    def testMeaningless(self):
        self.assertEquals(self.flatmeanings(englishdict, u"English"), None)

    def testMissingDictionary(self):
        self.assertEquals(fileSource('idontexist.txt'), None)
    
    def testMissingLanguage(self):
        dict = dictionaries('foobar')
        self.assertEquals(flatten(dict.reading(u"个")), "ge4")
        self.assertEquals(self.flatmeanings(dict, u"个"), None)
    
    def testGermanDictionary(self):
        self.assertEquals(flatten(germandict.reading(u"请")), "qing3")
        self.assertEquals(flatten(germandict.reading(u"請")), "qing3")
        self.assertEquals(self.flatmeanings(germandict, u"請"), ["Bitte ! (u.E.) (Int)", "bitten, einladen (u.E.) (V)"])

    def testEnglishDictionary(self):
        self.assertEquals(flatten(englishdict.reading(u"鼓聲")), "gu3 sheng1")
        self.assertEquals(flatten(englishdict.reading(u"鼓声")), "gu3 sheng1")
        self.assertEquals(self.flatmeanings(englishdict, u"鼓聲"), ["sound of a drum", "drumbeat"])

    def testFrenchDictionary(self):
        self.assertEquals(flatten(frenchdict.reading(u"白天")), "bai2 tian")
        self.assertEquals(flatten(frenchdict.reading(u"白天")), "bai2 tian")
        self.assertEquals(self.flatmeanings(frenchdict, u"白天"), [u"journée (n.v.) (n)"])

    def testWordsWhosePrefixIsNotInDictionary(self):
        self.assertEquals(flatten(germandict.reading(u"生日")), "sheng1 ri4")
        self.assertEquals(self.flatmeanings(germandict, u"生日"), [u"Geburtstag (S)"])

    def testProperName(self):
        self.assertEquals(flatten(englishdict.reading(u"珍・奥斯汀")), u"Zhen1 · Ao4 si1 ting1")
        self.assertEquals(self.flatmeanings(englishdict, u"珍・奥斯汀"), [u"Jane Austen (1775-1817), English novelist", u"also written 简・奥斯汀 - Jian3 · Ao4 si1 ting1"])

    def testShortPinyin(self):
        self.assertEquals(flatten(englishdict.reading(u"股指")), "gu3 zhi3")
        self.assertEquals(self.flatmeanings(englishdict, u"股指"), [u"stock market index", u"share price index", u"abbr. for 股票指数 - gu3 piao4 zhi3 shu4"])
    
    def testPinyinFromUnihan(self):
        self.assertEquals(flatten(englishdict.reading(u"噔")), "deng1")
        self.assertEquals(self.flatmeanings(englishdict, u"噔"), None)
    
    def testFrenchPinyinFallsBackOnCEDICT(self):
        self.assertEquals(flatten(frenchdict.reading(u"数量积")), "shu4 liang4 ji1")
        self.assertEquals(self.flatmeanings(frenchdict, u"数量积"), None)
    
    # I've changed my mind about this test. We can't really say that an occurance of 儿
    # was meant to be an erhua one without having an entry explicitly in the dictionary
    # for the erhua variant. This test used to pass with the old dictionary code because
    # it arbitrarily defaulted to the r5 reading rather than er4 as it does now.
    # def testErhuaNotSpacedInReadingEvenForUnknownWords(self):
    #         self.assertEquals(flatten(englishdict.reading(u"土豆条儿")), "tu3 dou4 tiao2r")

    # TODO: implement functionality
    # def testUsesFrequencyInformation(self):
    #         self.assertEquals(flatten(englishdict.reading(u"车")), "che1")
    #         self.assertEquals(flatten(englishdict.reading(u"教")), "jiao4")

    def testErhuaSpacedInReadingForKnownWords(self):
        self.assertEquals(flatten(englishdict.reading(u"两头儿")), "liang3 tou2r")

    def testSimpMeanings(self):
        self.assertEquals(self.flatmeanings(englishdict, u"书", prefersimptrad="simp"), [u"book", u"letter", u"same as 书经 Book of History", u"MW: 本 - ben3, 册 - ce4, 部 - bu4, 丛 - cong2"])
    
    def testTradMeanings(self):
        self.assertEquals(self.flatmeanings(englishdict, u"书", prefersimptrad="trad"), [u"book", u"letter", u"same as 書經 Book of History", u"MW: 本 - ben3, 冊 - ce4, 部 - bu4, 叢 - cong2"])
    
    def testNonFlatMeanings(self):
        dictmeanings, dictmeasurewords = englishdict.meanings(u"书", prefersimptrad="simp")
        self.assertEquals(self.flattenall(dictmeanings), [u"book", u"letter", u"same as 书经 Book of History"])
        self.assertEquals([(self.flattenall(dictmwcharacters)[0], self.flattenall(dictmwpinyin)[0]) for dictmwcharacters, dictmwpinyin in dictmeasurewords],
                          [(u"本", u"ben3"), (u"册", u"ce4"), (u"部", u"bu4"), (u"丛", u"cong2")])
    
    # Test helper 
    def flatmeanings(self, dictionary, what, prefersimptrad="simp"):
        dictmeanings = combinemeaningsmws(*(dictionary.meanings(what, prefersimptrad)))
        return self.flattenall(dictmeanings)
    
    def flattenall(self, tokens):
        if tokens:
            return [flatten(token) for token in tokens]
        else:
            return None

class PinyinConverterTest(unittest.TestCase):
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

    def testNoSpacesAfterBraces(self):
        self.assertEquals(self.reading(u"(你)好!"), u"(ni3)hao3!")

    def testEmptyString(self):
        self.assertEqual(self.reading(u""), u"")

    def testMixedEnglishChinese(self):
        self.assertEqual(self.reading(u"你 (pr.)"), u"ni3 (pr.)")

    def testNeutralRSuffix(self):
        self.assertEqual(self.reading(u"一塊兒"), "yi1 kuai4r")

    # Test helpers
    def reading(self, what):
        return flatten(englishdict.reading(what))