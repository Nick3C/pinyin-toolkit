# -*- coding: utf-8 -*-

import unittest

from pinyin.db import database
from pinyin.numbers import *


englishdict = dictionary.PinyinDictionary.loadall()('en')

class ReadingFromNumberlikeTest(unittest.TestCase):
    def testIntegerReading(self):
        self.assertReading("ba1 qian1 jiu3 bai3 er4 shi2 yi1", "8921")
        self.assertReading("ba1 qian1 jiu3 bai3 er4 shi2 yi1", "8,921")
        self.assertReading("san1 qian1 wan4 si4 bai3 wan4 san1 shi2 wan4 er4 wan4 si4 qian1 si4 bai3 san1 shi2 er4", "34,324,432")
    
    def testDecimalReading(self):
        self.assertReading("er4 shi2 wu3 dian3 er4 wu3", "25.25")
        self.assertReading("yi1 qian1 dian3 jiu3", "1,000.9")
        self.assertReading(None, "25.253,2")
    
    def testYearReading(self):
        self.assertReading("yi1 jiu3 jiu3 ba1 nian2", u"1998年")
        # This is not a very valid way of writing a year, but it's extra work to disallow it so what the hell
        self.assertReading("yi1 jiu3 jiu3 ba1 nian2", u"1,998年")
    
    def testPercentageReading(self):
        self.assertReading("bai3 fen1 zhi1 qi1 shi2", u"70%")
        self.assertReading("bai3 fen1 zhi1 qi1 shi2", u"70％")
        self.assertReading("bai3 fen1 zhi1 yi1 qian1", u"1000%")
        self.assertReading("bai3 fen1 zhi1 yi1 qian1", u"1,000%")
    
    def testFractionReading(self):
        self.assertReading("san1 fen1 zhi1 yi1", "1/3")
        self.assertReading("san1 fen1 zhi1 yi1", "1\\3")
        self.assertReading("san1 qian1 fen1 zhi1 yi1 qian1", "1,000/3,000")
    
    def testNoReadingForPhrase(self):
        self.assertReading(None, u"你好")
    
    def testNoReadingForBlank(self):
        self.assertReading(None, u"")
        self.assertReading(None, u"24.")
        self.assertReading(None, u"24/")
    
    def testNoReadingsIfTrailingStuff(self):
        self.assertReading(None, u"8921A")
        self.assertReading(None, u"8,921A")
        self.assertReading(None, u"25.25A")
        self.assertReading(None, u"1,000.9A")
        self.assertReading(None, u"1998年A")
        self.assertReading(None, u"80%A")
        self.assertReading(None, u"80％A")
        self.assertReading(None, u"1000%A")
        self.assertReading(None, u"1,000%A")
        self.assertReading(None, u"1/3A")
        self.assertReading(None, u"1\3A")
        self.assertReading(None, "1,000/3,000!")
    
    # Test helpers
    def assertReading(self, expected_reading, expression):
        self.assertEquals(expected_reading, utils.bind_none(readingfromnumberlike(expression, englishdict), lambda reading: model.flatten(reading)))

class MeaningFromNumberlikeTest(unittest.TestCase):
    def testIntegerMeaning(self):
        self.assertMeaning("8921", "8921")
        self.assertMeaning("8921", "8,921")
        self.assertMeaning("8921", u"八千九百二十一")
    
    def testDecimalMeaning(self):
        self.assertMeaning("25.25", "25.25")
        self.assertMeaning("25.25", u"25。25")
        self.assertMeaning("25.25", u"二十五点二五")
        self.assertMeaning("1123.89", u"1,123.89")
    
    def testYearMeaning(self):
        self.assertMeaning("1998AD", u"1998年")
        self.assertMeaning("1998AD", u"一九九八年")
    
    def testPercentageReading(self):
        self.assertMeaning("20%", u"20%")
        self.assertMeaning("1000%", u"1000%")
        self.assertMeaning("1000%", u"1,000%")
        self.assertMeaning("20%", u"百分之二十")
    
    def testFractionReading(self):
        self.assertMeaning("1/3", u"1/3")
        self.assertMeaning("1000/3000", u"1,000/3,000")
        self.assertMeaning("1/3", u"三分之一")
    
    def testNoMeaningForPhrase(self):
        self.assertMeaning(None, u"你好")
    
    def testNoMeaningForBlank(self):
        self.assertMeaning(None, u"")
        self.assertMeaning(None, u"24.")
    
    def testNoMeaningsIfTrailingStuff(self):
        self.assertMeaning(None, u"8921A")
        self.assertMeaning(None, u"8,921A")
        self.assertMeaning(None, u"八千九百二十一A")
        self.assertMeaning(None, u"25.25A")
        self.assertMeaning(None, u"25。25A")
        self.assertMeaning(None, u"二十五点二五A")
        self.assertMeaning(None, u"1,123.89A")
        self.assertMeaning(None, u"1998年A")
        self.assertMeaning(None, u"一九九八年A")
        self.assertMeaning(None, u"100%A")
        self.assertMeaning(None, u"1000%Junk")
        self.assertMeaning(None, u"1,000%!")
        self.assertMeaning(None, u"百分之二十A")
        self.assertMeaning(None, u"1/3A")
        self.assertMeaning(None, u"1\3A")
        self.assertMeaning(None, u"1,000/3,000Blah")
        self.assertMeaning(None, u"三分之一A")
    
    # Test helpers
    def assertMeaning(self, expected_meaning, expression):
        self.assertEquals(expected_meaning, utils.bind_none(meaningfromnumberlike(expression, englishdict), lambda meanings: model.flatten(meanings[0])))

class NumberAsHanziTest(unittest.TestCase):
    def testSingleNumerals(self):
        self.assertEquals(numberashanzi(0), u"零")
        self.assertEquals(numberashanzi(5), u"五")
        self.assertEquals(numberashanzi(9), u"九")
    
    def testTooLargeNumber(self):
        self.assertEquals(numberashanzi(100000000000000000), u"100000000000000000")
    
    def testFullNumbers(self):
        self.assertEquals(numberashanzi(25), u"二十五")
        self.assertEquals(numberashanzi(8921), u"八千九百二十一")
    
    def testTruncationOfLowerUnits(self):
        self.assertEquals(numberashanzi(20), u"二十")
        self.assertEquals(numberashanzi(9000), u"九千")
        self.assertEquals(numberashanzi(9100), u"九千一百")

    def testSkippedOnes(self):
        self.assertEquals(numberashanzi(1), u"一")
        self.assertEquals(numberashanzi(10), u"十")
        self.assertEquals(numberashanzi(100), u"百")
        self.assertEquals(numberashanzi(1000), u"一千")

    def testSkippedMagnitudes(self):
        self.assertEquals(numberashanzi(9025), u"九千零二十五")
        self.assertEquals(numberashanzi(9020), u"九千零二十")
        self.assertEquals(numberashanzi(9005), u"九千零五")

class HanziAsNumberTest(unittest.TestCase):
    def testSingleNumerals(self):
        self.assertHanziAsNumber(u"零", 0)
        self.assertHanziAsNumber(u"五", 5)
        self.assertHanziAsNumber(u"九", 9)
    
    def testLing(self):
        self.assertHanziAsNumber(u"零", 0)
        self.assertHanziAsNumber(u"零个", 0, expected_rest_hanzi=u"个")
    
    def testLiang(self):
        self.assertHanziAsNumber(u"两", 2)
        self.assertHanziAsNumber(u"两个", 2, expected_rest_hanzi=u"个")
    
    def testFullNumbers(self):
        self.assertHanziAsNumber(u"二十五", 25)
        self.assertHanziAsNumber(u"八千九百二十一", 8921)
    
    def testTruncationOfLowerUnits(self):
        self.assertHanziAsNumber(u"二十", 20)
        self.assertHanziAsNumber(u"九千", 9000)
        self.assertHanziAsNumber(u"九千一百", 9100)

    def testSkippedOnes(self):
        self.assertHanziAsNumber(u"一", 1)
        self.assertHanziAsNumber(u"十", 10)
        self.assertHanziAsNumber(u"百", 100)
        self.assertHanziAsNumber(u"一千", 1000)

    def testSkippedMagnitudes(self):
        self.assertHanziAsNumber(u"九千零二十五", 9025)
        self.assertHanziAsNumber(u"九千零二十", 9020)
        self.assertHanziAsNumber(u"九千零五", 9005)
    
    def testNonNumber(self):
        self.assertHanziAsNumber(u"一个", 1, expected_rest_hanzi=u"个")
        self.assertHanziAsNumber(u"个", None, expected_rest_hanzi=u"个")

    # Test helpers
    def assertHanziAsNumber(self, hanzi, expect_number, expected_rest_hanzi=""):
        actual_number, actual_rest_hanzi = parsehanziasnumber(hanzi)
        self.assertEquals(actual_rest_hanzi, expected_rest_hanzi)
        self.assertEquals(actual_number, expect_number)