# -*- coding: utf-8 -*-

import unittest

import pinyin.dictionary
from pinyin.model import *


englishdict = pinyin.dictionary.PinyinDictionary.loadall()('en')

class ToneInfoTest(unittest.TestCase):
    def testAccessors(self):
        ti = ToneInfo(written=1, spoken=2)
        self.assertEquals(ti.written, 1)
        self.assertEquals(ti.spoken, 2)
    
    def testRepr(self):
        self.assertEquals(repr(ToneInfo(written=1, spoken=2)), "ToneInfo(written=1, spoken=2)")
    
    def testDefaulting(self):
        self.assertEquals(ToneInfo(written=1), ToneInfo(written=1, spoken=1))
        self.assertEquals(ToneInfo(spoken=1), ToneInfo(written=1, spoken=1))
    
    def testEq(self):
        self.assertEquals(ToneInfo(written=1, spoken=3), ToneInfo(written=1, spoken=3))
        self.assertNotEquals(ToneInfo(written=1, spoken=3), ToneInfo(written=2, spoken=3))
        self.assertNotEquals(ToneInfo(written=1, spoken=3), ToneInfo(written=1, spoken=5))
    
    def testEqDissimilar(self):
        self.assertNotEquals(ToneInfo(written=1, spoken=3), "ToneInfo(written=1, spoken=3)")
        self.assertNotEquals("ToneInfo(written=1, spoken=3)", ToneInfo(written=1, spoken=3))

    def testMustBeNonEmpty(self):
        self.assertRaises(ValueError, lambda: ToneInfo())

class PinyinTest(unittest.TestCase):
    def testConvenienceConstructor(self):
        self.assertEquals(Pinyin(u"hen", 3), Pinyin(u"hen", ToneInfo(written=3)))
    
    def testUnicode(self):
        self.assertEquals(unicode(Pinyin(u"hen", 3)), u"hen3")
    
    def testStr(self):
        self.assertEquals(str(Pinyin(u"hen", 3)), u"hen3")
    
    def testRepr(self):
        self.assertEquals(repr(Pinyin(u"hen", 3)), u"Pinyin(u'hen', ToneInfo(written=3, spoken=3))")
        self.assertEquals(repr(Pinyin(u"hen", 3, { "attr" : "val" })), u"Pinyin(u'hen', ToneInfo(written=3, spoken=3), {'attr': 'val'})")
    
    def testEq(self):
        self.assertEquals(Pinyin(u"hen", 3), Pinyin(u"hen", 3))
        self.assertEquals(Pinyin(u"hen", 3, { "moo" : "cow" }), Pinyin(u"hen", 3, { "moo" : "cow" }))
        self.assertNotEquals(Pinyin(u"hen", 3), Pinyin(u"hen", 2))
        self.assertNotEquals(Pinyin(u"hen", 3), Pinyin(u"han", 3))
        self.assertNotEquals(Pinyin(u"hen", 3), Pinyin(u"hen", 3, { "moo" : "cow" }))
        self.assertNotEquals(Pinyin(u"hen", 3, { "moo" : "cow" }), Pinyin(u"hen", 3, { "moo" : "sheep" }))
    
    def testEqDissimilar(self):
        self.assertNotEquals(Pinyin(u"hen", 3), "Pinyin(u'hen', 3)")
        self.assertNotEquals("Pinyin(u'hen', 3)", Pinyin(u"hen", 3))
    
    def testStrNeutralTone(self):
        py = Pinyin(u"ma", 5)
        self.assertEquals(str(py), u"ma")
    
    def testNumericFormat(self):
        self.assertEquals(Pinyin(u"hen", 3).numericformat(), u"hen3")
    
    def testNumericFormatSelectTone(self):
        self.assertEquals(Pinyin(u"hen", ToneInfo(written=1, spoken=2)).numericformat(tone="written"), u"hen1")
        self.assertEquals(Pinyin(u"hen", ToneInfo(written=1, spoken=2)).numericformat(tone="spoken"), u"hen2")
        
    def testNumericFormatNeutralTone(self):
        self.assertEquals(Pinyin(u"ma", 5).numericformat(), u"ma5")
        self.assertEquals(Pinyin(u"ma", 5).numericformat(hideneutraltone=True), u"ma")
    
    def testTonifiedFormat(self):
        self.assertEquals(Pinyin(u"hen", 3).tonifiedformat(), u"hěn")
    
    def testTonifiedFormatNeutralTone(self):
        self.assertEquals(Pinyin(u"ma", 5).tonifiedformat(), u"ma")
    
    def testIsEr(self):
        self.assertTrue(Pinyin(u"r", 5).iser)
        self.assertTrue(Pinyin(u"R", 5).iser)
        self.assertFalse(Pinyin(u"r", 4).iser)
        self.assertFalse(Pinyin(u"er", 5).iser)
    
    def testParse(self):
        self.assertEquals(Pinyin.parse("ma1"), Pinyin("ma", 1))
        self.assertEquals(Pinyin.parse("ma2"), Pinyin("ma", 2))
        self.assertEquals(Pinyin.parse("ma3"), Pinyin("ma", 3))
        self.assertEquals(Pinyin.parse("ma4"), Pinyin("ma", 4))
        self.assertEquals(Pinyin.parse("ma5"), Pinyin("ma", 5))
    
    def testParseAdditions(self):
        self.assertEquals(Pinyin.parse("er5"), Pinyin("er", 5))
        self.assertEquals(Pinyin.parse("r2"), Pinyin("r", 2))
    
    def testParseShort(self):
        self.assertEquals(Pinyin.parse("a1"), Pinyin("a", 1))
    
    def testParseLong(self):
        self.assertEquals(Pinyin.parse("zhuang1"), Pinyin("zhuang", 1))
    
    def testParseNormalisesUmlaut(self):
        self.assertEquals(Pinyin.parse("nu:3"), Pinyin.parse(u"nü3"))
        self.assertEquals(Pinyin.parse("nU:3"), Pinyin.parse(u"nÜ3"))
        self.assertEquals(Pinyin.parse("nv3"), Pinyin.parse(u"nü3"))
        self.assertEquals(Pinyin.parse("nV3"), Pinyin.parse(u"nÜ3"))
    
    def testParseTonified(self):
        self.assertEquals(Pinyin.parse("chi1"), Pinyin.parse(u"chī"))
        self.assertEquals(Pinyin.parse("shi2"), Pinyin.parse(u"shí"))
        self.assertEquals(Pinyin.parse("xiao3"), Pinyin.parse(u"xiǎo"))
        self.assertEquals(Pinyin.parse("dan4"), Pinyin.parse(u"dàn"))
        self.assertEquals(Pinyin.parse("huan"), Pinyin.parse(u"huan"))
    
    def testParseRespectsOtherCombiningMarks(self):
        self.assertEquals(u"nü", unicode(Pinyin.parse(u"nü5")))
        self.assertEquals(u"nü", unicode(Pinyin.parse(u"nü")))
    
    def testParseForceNumeric(self):
        Pinyin.parse("chi")
        self.assertRaises(ValueError, lambda: Pinyin.parse("chi", forcenumeric=True))
    
    def testParseUnicode(self):
        self.assertEquals(repr(Pinyin.parse(u"nü3")), u"Pinyin(u'n\\xfc', ToneInfo(written=3, spoken=3))")
    
    def testParseAlternativeUUmlaut(self):
        self.assertEquals(Pinyin.parse(u"nü3"), Pinyin.parse(u"nu:3"))
        self.assertEquals(Pinyin.parse(u"nü3"), Pinyin.parse(u"nv3"))
        self.assertEquals(Pinyin.parse(u"lü3"), Pinyin.parse(u"lu:3"))
    
    # Bug #138 - kind of a relic of when we used a regex to recognise pinyin
    def testParsesXiong(self):
        self.assertEquals(Pinyin.parse(u"xiong1"), Pinyin("xiong", 1))
    
    def testRejectsPinyinWithMultipleToneMarks(self):
        self.assertRaises(ValueError, lambda: Pinyin.parse(u"xíǎo"))
    
    def testRejectsSingleNumbers(self):
        self.assertRaises(ValueError, lambda: Pinyin.parse(u"1"))
    
    def testRejectsNumbers(self):
        self.assertRaises(ValueError, lambda: Pinyin.parse(u"12345"))
    
    def testRejectsPinyinlikeEnglish(self):
        self.assertRaises(ValueError, lambda: Pinyin.parse("USB"))

class TextTest(unittest.TestCase):
    def testNonEmpty(self):
        self.assertRaises(ValueError, lambda: Text(u""))
    
    def testRepr(self):
        self.assertEquals(repr(Text(u"hello")), "Text(u'hello')")
        self.assertEquals(repr(Text(u"hello", { "china" : "great" })), "Text(u'hello', {'china': 'great'})")
    
    def testUnicodeAndStr(self):
        self.assertEquals(str(Text(u"hello")), u"hello")
        self.assertEquals(unicode(Text(u"hello")), u"hello")
        self.assertEquals(type(unicode(Text(u"hello"))), unicode)
    
    def testEq(self):
        self.assertEquals(Text(u"hello"), Text(u"hello"))
        self.assertEquals(Text(u"hello", { "color" : "mah" }), Text(u"hello", { "color" : "mah" }))
        self.assertNotEquals(Text(u"hello"), Text(u"bye"))
        self.assertNotEquals(Text(u"hello", { "color" : "mah" }), Text(u"hello"))
        self.assertNotEquals(Text(u"hello", { "color" : "mah" }), Text(u"hello", { "color" : "meh" }))
    
    def testEqDissimilar(self):
        self.assertNotEquals(Text(u"hello"), 'Text(u"hello")')
        self.assertNotEquals('Text(u"hello")', Text(u"hello"))
    
    def testIsEr(self):
        self.assertFalse(Text("r5").iser)

class WordTest(unittest.TestCase):
    def testEquality(self):
        self.assertEquals(Word(Text(u"hello")), Word(Text(u"hello")))
        self.assertNotEquals(Word(Text(u"hello")), Word(Text(u"hallo")))
    
    def testRepr(self):
        self.assertEquals(repr(Word(Text(u"hello"))), "Word(Text(u'hello'))")
    
    def testStr(self):
        self.assertEquals(str(Word(Text(u"hello"))), u"<hello>")
        self.assertEquals(unicode(Word(Text(u"hello"))), u"<hello>")
        
    def testFilterNones(self):
        self.assertEquals(Word(None, Text("yes"), None, Text("no")), Word(Text("yes"), Text("no")))
    
    def testAppendNoneFiltered(self):
        word = Word(Text("yes"), Text("no"))
        word.append(None)
        self.assertEquals(word, Word(Text("yes"), Text("no")))
    
    def testExtend(self):
        word = Word(Text(u"hello"))
        word.extend([Text(u"world"), None, Text(u"above")])
        self.assertEquals(word, Word(Text(u"hello"), Text(u"world"), Text(u"above")))

    def testAccept(self):
        output = []
        class Visitor(object):
            def visitText(self, text):
                output.append(text)
            
            def visitPinyin(self, pinyin):
                output.append(pinyin)
            
            def visitTonedCharacter(self, tonedcharacter):
                output.append(tonedcharacter)
        
        Word(Text("Hi"), Pinyin.parse("hen3"), TonedCharacter("a", 2), Text("Bye")).accept(Visitor())
        self.assertEqual(output, [Text("Hi"), Pinyin.parse("hen3"), TonedCharacter("a", 2), Text("Bye")])
    
    def testMap(self):
        class Visitor(object):
            def visitText(self, text):
                return Text("MEH")
            
            def visitPinyin(self, pinyin):
                return Pinyin.parse("hai3")
            
            def visitTonedCharacter(self, tonedcharacter):
                return TonedCharacter("M", 2)
        
        self.assertEqual(Word(Text("Hi"), Pinyin.parse("hen3"), TonedCharacter("a", 2), Text("Bye")).map(Visitor()),
                         Word(Text("MEH"), Pinyin.parse("hai3"), TonedCharacter("M", 2), Text("MEH")))
    
    def testConcatMap(self):
        class Visitor(object):
            def visitText(self, text):
                return []
            
            def visitPinyin(self, pinyin):
                return [pinyin, pinyin]
            
            def visitTonedCharacter(self, tonedcharacter):
                return [TonedCharacter("M", 2)]
        
        self.assertEqual(Word(Text("Hi"), Pinyin.parse("hen3"), TonedCharacter("a", 2), Text("Bye")).concatmap(Visitor()),
                         Word(Pinyin.parse("hen3"), Pinyin.parse("hen3"), TonedCharacter("M", 2)))

class TonedCharacterTest(unittest.TestCase):
    def testConvenienceConstructor(self):
        self.assertEquals(TonedCharacter(u"儿", 2), TonedCharacter(u"儿", ToneInfo(written=2)))
    
    def testRepr(self):
        self.assertEquals(repr(TonedCharacter(u"儿", 2)), "TonedCharacter(u'\\u513f', ToneInfo(written=2, spoken=2))")
        self.assertEquals(repr(TonedCharacter(u"儿", ToneInfo(written=2, spoken=3), { "foo" : "bar" })), "TonedCharacter(u'\\u513f', ToneInfo(written=2, spoken=3), {'foo': 'bar'})")
    
    def testEq(self):
        self.assertEquals(TonedCharacter(u"儿", 2), TonedCharacter(u"儿", 2))
        self.assertEquals(TonedCharacter(u"儿", 2, { "color" : "meh" }), TonedCharacter(u"儿", 2, { "color" : "meh" }))
        self.assertNotEquals(TonedCharacter(u"儿", 2), TonedCharacter(u"儿", 3))
        self.assertNotEquals(TonedCharacter(u"儿", 2), TonedCharacter(u"兒", 2))
        self.assertNotEquals(TonedCharacter(u"儿", 2), TonedCharacter(u"儿", 2, { "foo" : "bar" }))
        self.assertNotEquals(TonedCharacter(u"儿", 2, { "color" : "moo" }), TonedCharacter(u"儿", 2, { "color" : "meh" }))
    
    def testEqDissimilar(self):
        self.assertNotEquals(TonedCharacter(u"儿", 2), "TonedCharacter(u'儿', 2)")
        self.assertNotEquals("TonedCharacter(u'儿', 2)", TonedCharacter(u"儿", 2))
    
    def testIsEr(self):
        self.assertTrue(TonedCharacter(u"儿", 5).iser)
        self.assertTrue(TonedCharacter(u"兒", 5).iser)
        self.assertFalse(TonedCharacter(u"化", 2).iser)
        self.assertFalse(TonedCharacter(u"儿", 4).iser)

class TokenizeSpaceSeperatedTextTest(unittest.TestCase):
    def testFromSingleSpacedString(self):
        self.assertEquals([Pinyin.parse(u"hen3")], tokenizespaceseperatedtext(u"hen3"))

    def testFromMultipleSpacedString(self):
        self.assertEquals([Pinyin.parse(u"hen3"), Pinyin.parse(u"hao3")], tokenizespaceseperatedtext(u"hen3 hao3"))

    def testFromSpacedStringWithEnglish(self):
        self.assertEquals([Text(u"T"), Pinyin.parse(u"xu4")], tokenizespaceseperatedtext(u"T xu4"))

    def testFromSpacedStringWithPinyinlikeEnglish(self):
        self.assertEquals([Text(u"USB"), Pinyin.parse(u"xu4")], tokenizespaceseperatedtext(u"USB xu4"))

class TokenizeTest(unittest.TestCase):
    def testTokenizeSimple(self):
        self.assertEquals([Pinyin.parse(u"hen3"), Text(" "), Pinyin.parse(u"hao3")], tokenize(u"hen3 hao3"))
        self.assertEquals([Pinyin.parse(u"hen3"), Text(","), Pinyin.parse(u"hao3")], tokenize(u"hen3,hao3"))
        self.assertEquals([Pinyin.parse(u"hen3"), Text(" "), Pinyin.parse(u"hao3"), Text(", "), Text("my"), Text(" "), Pinyin.parse(u"xiǎo"), Text(" "), Text("one"), Text("!")],
                          tokenize(u"hen3 hao3, my xiǎo one!"))
    
    def testTokenizeUUmlaut(self):
        self.assertEquals([Pinyin.parse(u"lu:3")], tokenize(u"lu:3"))
    
    def testTokenizeErhua(self):
        self.assertEquals([Pinyin.parse(u"wan4"), Pinyin(u"r", 5)], tokenize(u"wan4r"))
        self.assertEquals([Text(u"color")], tokenize(u"color"))
    
    def testTokenizeForceNumeric(self):
        self.assertEquals([Pinyin.parse(u"hen3"), Text(" "), Pinyin.parse(u"hao3")], tokenize(u"hen3 hao3"))
        self.assertEquals([Pinyin.parse(u"hen3"), Text(" "), Pinyin.parse(u"hao3"), Text(", "), Text("my"), Text(" "), Text(u"xiǎo"), Text(" "), Text("one"), Text("!")],
                           tokenize(u"hen3 hao3, my xiǎo one!", forcenumeric=True))
    
    def testTokenizeHTML(self):
        self.assertEquals([Text(u'<b>'), Text("some"), Text(" "), Text("silly"), Text(" "), Text("text"), Text("</b>")],
                          tokenize(u'<b>some silly text</b>'))
        self.assertEquals([Text(u'<span style="">'), Pinyin(u'tou', 2, { "color" : "#123456" }), Text(u'</span>'), Text(u' '), Text(u'<span style="">'), Pinyin(u'er', 4, { "color" : "#123456" }), Text(u'</span>')],
                          tokenize(u'<span style="color:#123456">tou2</span> <span style="color:#123456">er4</span>'))
    
    def testTokenizeUnrecognisedHTML(self):
        self.assertEquals([Text(u'<b>'), Text(u'</b>')], tokenize(u'<b />'))
        self.assertEquals([Text(u'<span style="mehhhh!">'), Text("</span>")], tokenize(u'<span style="mehhhh!"></span>'))

    def testTokenizeWeirdyRomanCharacters(self):
        self.assertEquals([Text(u'Ｕ')], tokenize(u'Ｕ'))

class FormatReadingForDisplayTest(unittest.TestCase):
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

    def testSimpleSingleton(self):
        self.assertEquals(self.format([Word(Pinyin.parse(u"hen3"))]), u"hen3")

    def testSimpleSpacing(self):
        self.assertEquals(self.format([Word(Pinyin.parse(u"hen3"), Pinyin.parse(u"ma5"))]), u"hen3 ma")

    def testSimpleErhuaSingleton(self):
        self.assertEquals(self.format([Word(Pinyin.parse(u"r5"))]), u"r")

    def testSimpleErhua(self):
        self.assertEquals(self.format([Word(Pinyin.parse(u"hen3"), Pinyin.parse(u"ma5"), Pinyin.parse("r5"))]), u"hen3 mar")

    def testSimpleTonedCharacter(self):
        self.assertEquals(self.format([Word(TonedCharacter(u"塊", 1))]), u"塊")

    def testErhuaNextToText(self):
        self.assertEquals(self.format([Word(Text("not pinyin"), Pinyin.parse(u"r5"))]), u"not pinyin r")

    def testErhuaNextToPinyinInOtherWord(self):
        self.assertEquals(self.format([Word(Pinyin.parse(u"hen3")), Word(Pinyin.parse(u"r5"))]), u"hen3r")

    # Test helpers
    def format(self, what):
        return flatten(formatreadingfordisplay(what))
    
    def reading(self, what):
        return self.format(englishdict.reading(what))

class UnformatReadingForDisplayTest(unittest.TestCase):
    def testNoUnformatting(self):
        self.assertEquals(self.unformat([Word(Text("not pinyin"), Pinyin.parse(u"ni3"), TonedCharacter(u"一", 1))]), u"not pinyinni3一")
    
    def testUnformatting(self):
        self.assertEquals(self.unformat([Word(Pinyin.parse(u"ni3"), Text(" "), Pinyin.parse(u"hao3"), Text("\ttons more junk!! "), )]), u"ni3hao3tons more junk!!")
    
    # Test helpers
    def unformat(self, what):
        return flatten(unformatreadingfordisplay(what))

class PinyinTonifierTest(unittest.TestCase):
    def testEasy(self):
        self.assertEquals(PinyinTonifier().tonify(u"Han4zi4 bu4 mie4, Zhong1guo2 bi4 wang2!"),
                          u"Hànzì bù miè, Zhōngguó bì wáng!")

    def testObscure(self):
        self.assertEquals(PinyinTonifier().tonify(u"huai4"), u"huài")

    def testUpperCase(self):
        self.assertEquals(PinyinTonifier().tonify(u"Huai4"), u"Huài")
        self.assertEquals(PinyinTonifier().tonify(u"An1 hui1 sheng3"), u"Ān huī shěng")
    
    def testGreeting(self):
        self.assertEquals(PinyinTonifier().tonify(u"ni3 hao3, wo3 xi3 huan xue2 xi2 Han4 yu3. wo3 de Han4 yu3 shui3 ping2 hen3 di1."),
                          u"nǐ hǎo, wǒ xǐ huan xué xí Hàn yǔ. wǒ de Hàn yǔ shuǐ píng hěn dī.")

class FlattenTest(unittest.TestCase):
    def testFlatten(self):
        self.assertEquals(flatten([Word(Text(u'a ')), Word(Pinyin.parse(u"hen3"), Text(u' b')), Word(Text(u"junk")), Word(Pinyin.parse(u"ma5"))]),
                          u"a hen3 bjunkma")
        
    def testFlattenTonified(self):
        self.assertEquals(flatten([Word(Text(u'a ')), Word(Pinyin.parse(u"hen3"), Text(u' b')), Word(Text(u"junk")), Word(Pinyin.parse(u"ma5"))], tonify=True),
                          u"a hěn bjunkma")
    
    def testUsesWrittenTone(self):
        self.assertEquals(flatten([Word(Pinyin("hen", ToneInfo(written=2,spoken=3)))]), "hen2")

class TonedCharactersFromReadingTest(unittest.TestCase):
    def testTonedTokens(self):
        self.assertEquals(tonedcharactersfromreading(u"一个", [Word(Pinyin.parse("yi1"), Pinyin.parse("ge4"))]),
                          [Word(TonedCharacter(u"一", 1), TonedCharacter(u"个", 4))])

    def testTonedTokensWithoutTone(self):
        self.assertEquals(tonedcharactersfromreading(u"T恤", [Word(Text("T"), Pinyin.parse("zhi4"))]),
                          [Word(Text(u"T"), TonedCharacter(u"恤", 4))])

    def testTonedTokenNumbers(self):
        self.assertEquals(tonedcharactersfromreading(u"1994", [Word(Pinyin.parse("yi1"), Pinyin.parse("jiu3"), Pinyin.parse("jiu3"), Pinyin.parse("si4"))]),
                          [Word(Text(u"1"), Text(u"9"), Text(u"9"), Text(u"4"))])
    
    def testTonesDontMatchChars(self):
        self.assertEquals(tonedcharactersfromreading(u"ABCD", [Word(Pinyin.parse("yi1"), Pinyin.parse("shi2"), Pinyin.parse("jiu3"), Pinyin.parse("jiu3"), Pinyin.parse("shi2"), Pinyin.parse("si4"))]),
                          [Word(Text(u"ABCD"))])
        self.assertEquals(tonedcharactersfromreading(u"ABCD", [Word(Pinyin.parse("yi1"))]),
                          [Word(Text(u"ABCD"))])