# -*- coding: utf-8 -*-

import unittest

from pinyin.model import *


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
    
    def testEq(self):
        self.assertEquals(Text(u"hello"), Text(u"hello"))
        self.assertNotEquals(Text(u"hello"), Text(u"bye"))
    
    def testEqDissimilar(self):
        self.assertNotEquals(Text(u"hello"), 'Text(u"hello")')
        self.assertNotEquals('Text(u"hello")', Text(u"hello"))
    
    def testIsEr(self):
        self.assertFalse(Text("r5").iser)

class WordTest(unittest.TestCase):
    def testAppendSingleReading(self):
        self.assertEquals(flatten([Word.spacedwordfromunspacedtokens([Pinyin.parse(u"hen3")])]), u"hen3")

    def testAppendMultipleReadings(self):
        self.assertEquals(flatten([Word.spacedwordfromunspacedtokens([Pinyin.parse(u"hen3"), Pinyin.parse(u"ma5")])]), u"hen3 ma")
    
    def testAppendSingleReadingErhua(self):
        self.assertEquals(flatten([Word.spacedwordfromunspacedtokens([Pinyin.parse(u"r5")])]), u"r")

    def testAppendMultipleReadingsErhua(self):
        self.assertEquals(flatten([Word.spacedwordfromunspacedtokens([Pinyin.parse(u"hen3"), Pinyin.parse(u"ma5"), Pinyin.parse("r5")])]), u"hen3 mar")
    
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
    
    def testEq(self):
        self.assertEquals(TonedCharacter(u"儿", 2), TonedCharacter(u"儿", 2))
        self.assertNotEquals(TonedCharacter(u"儿", 2), TonedCharacter(u"儿", 3))
        self.assertNotEquals(TonedCharacter(u"儿", 2), TonedCharacter(u"兒", 2))
    
    def testEqDissimilar(self):
        self.assertNotEquals(TonedCharacter(u"儿", 2), "TonedCharacter(u'儿', 2)")
        self.assertNotEquals("TonedCharacter(u'儿', 2)", TonedCharacter(u"儿", 2))
    
    def testIsEr(self):
        self.assertTrue(TonedCharacter(u"儿", 5).iser)
        self.assertTrue(TonedCharacter(u"兒", 5).iser)
        self.assertFalse(TonedCharacter(u"化", 2).iser)
        self.assertFalse(TonedCharacter(u"儿", 4).iser)

class TokenizeSpaceSeperatedTest(unittest.TestCase):
    def testFromSingleSpacedString(self):
        self.assertEquals([Pinyin.parse(u"hen3")], tokenizespaceseperated(u"hen3"))

    def testFromMultipleSpacedString(self):
        self.assertEquals([Pinyin.parse(u"hen3"), Pinyin.parse(u"hao3")], tokenizespaceseperated(u"hen3 hao3"))

    def testFromSpacedStringWithEnglish(self):
        self.assertEquals([Text(u"T"), Pinyin.parse(u"xu4")], tokenizespaceseperated(u"T xu4"))

    def testFromSpacedStringWithPinyinlikeEnglish(self):
        self.assertEquals([Text(u"USB"), Pinyin.parse(u"xu4")], tokenizespaceseperated(u"USB xu4"))

class TokenizeTest(unittest.TestCase):
    def testTokenizeSimple(self):
        self.assertEquals([Pinyin.parse(u"hen3"), Text(" "), Pinyin.parse(u"hao3")], tokenize(u"hen3 hao3"))
        self.assertEquals([Pinyin.parse(u"hen3"), Text(","), Pinyin.parse(u"hao3")], tokenize(u"hen3,hao3"))
        self.assertEquals([Pinyin.parse(u"hen3"), Text(" "), Pinyin.parse(u"hao3"), Text(", "), Text("my"), Text(" "), Pinyin.parse(u"xiǎo"), Text(" "), Text("one"), Text("!")],
                          tokenize(u"hen3 hao3, my xiǎo one!"))
    
    def testTokenizeErhua(self):
        self.assertEquals([Pinyin.parse(u"wan4"), Pinyin(u"r", 5)], tokenize(u"wan4r"))
        self.assertEquals([Text(u"color")], tokenize(u"color"))
    
    def testTokenizeForceNumeric(self):
      self.assertEquals([Pinyin.parse(u"hen3"), Text(" "), Pinyin.parse(u"hao3")], tokenize(u"hen3 hao3"))
      self.assertEquals([Pinyin.parse(u"hen3"), Text(" "), Pinyin.parse(u"hao3"), Text(", "), Text("my"), Text(" "), Text(u"xiǎo"), Text(" "), Text("one"), Text("!")],
                        tokenize(u"hen3 hao3, my xiǎo one!", forcenumeric=True))
    
    def testTokenizeHTML(self):
        self.assertEquals([Text(u'<'), Text(u'span'), Text(u' '), Text(u'style'), Text(u'="'), Text(u'color'), Text(u':#'), Text(u'123456'), Text(u'">'),
                           Pinyin(u'tou', ToneInfo(written=2, spoken=2)), Text(u'</'), Text(u'span'), Text(u'> <'), Text(u'span'), Text(u' '), Text(u'style'),
                           Text(u'="'), Text(u'color'), Text(u':#'), Text(u'123456'), Text(u'">'), Pinyin(u'er', ToneInfo(written=4, spoken=4)), Text(u'</'), Text(u'span'), Text(u'>')],
                           tokenize(u'<span style="color:#123456">tou2</span> <span style="color:#123456">er4</span>'))

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

class NeedsSpaceBeforeAppendTest(unittest.TestCase):
    def testEmptyDoesntNeedSpace(self):
        self.assertFalse(needsspacebeforeappend([]))
    
    def testEndsWithWhitespace(self):
        self.assertFalse(needsspacebeforeappend([Word(Text("hello "))]))
        self.assertFalse(needsspacebeforeappend([Word(Text("hello"), Text(" "), Text("World"), Text(" "))]))
        self.assertFalse(needsspacebeforeappend([Word(Text("hello"), Text(" "), Text("World"), Text("!\t"))]))
    
    def testNeedsSpace(self):
        self.assertTrue(needsspacebeforeappend([Word(Text("hello"))]))
    
    def testPunctuation(self):
        self.assertTrue(needsspacebeforeappend([Word(Text("."))]))
        self.assertTrue(needsspacebeforeappend([Word(Text(","))]))
        self.assertFalse(needsspacebeforeappend([Word(Text("("))]))
        self.assertFalse(needsspacebeforeappend([Word(Text(")"))]))
        self.assertFalse(needsspacebeforeappend([Word(Text('"'))]))

class TonedCharactersFromReadingTest(unittest.TestCase):
    def testTonedTokens(self):
        self.assertEquals(tonedcharactersfromreading(u"一个", [Pinyin.parse("yi1"), Pinyin.parse("ge4")]),
                          [TonedCharacter(u"一", 1), TonedCharacter(u"个", 4)])

    def testTonedTokensWithoutTone(self):
        self.assertEquals(tonedcharactersfromreading(u"T恤", [Text("T"), Pinyin.parse("zhi4")]),
                          [Text(u"T"), TonedCharacter(u"恤", 4)])

    def testTonedTokenNumbers(self):
        self.assertEquals(tonedcharactersfromreading(u"1994", [Pinyin.parse("yi1"), Pinyin.parse("jiu3"), Pinyin.parse("jiu3"), Pinyin.parse("si4")]),
                          [Text(u"1"), Text(u"9"), Text(u"9"), Text(u"4")])
    
    def testTonesDontMatchChars(self):
        self.assertEquals(tonedcharactersfromreading(u"ABCD", [Pinyin.parse("yi1"), Pinyin.parse("shi2"), Pinyin.parse("jiu3"), Pinyin.parse("jiu3"), Pinyin.parse("shi2"), Pinyin.parse("si4")]),
                          [Text(u"ABCD")])