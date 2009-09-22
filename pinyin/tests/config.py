# -*- coding: utf-8 -*-

import unittest

from pinyin.config import *


class ConfigTest(unittest.TestCase):
    def testPickle(self):
        import pickle
        config = Config({ "setting" : "value", "cheese" : "mice" })
        self.assertEquals(pickle.loads(pickle.dumps(config)).settings, config.settings)

    def testAttribute(self):
        self.assertEquals(Config({ "tonedisplay" : "value" }).tonedisplay, "value")
    
    def testIndexedAttribute(self):
        self.assertEquals(Config({ "tonecolors" : ["100"] }).tonecolors[0], "100")

    def testMissingAttribute(self):
        self.assertRaises(AttributeError, lambda: Config({ "key" : ["value"] }).kay)
    
    def testNonExistentKeysDiscarded(self):
        self.assertRaises(AttributeError, lambda: Config({ "idontexist" : "value" }).idontexist)
    
    def testNonExistentFieldNamesDiscarded(self):
        self.assertRaises(KeyError, lambda: Config({ "candidateFieldNamesByKey" : { "silly" : ["Fish"] } }).candidateFieldNamesByKey["silly"])
    
    def testPositionalListLengthNotChanged(self):
        config = Config({ "tonecolors" : ["hi"] })
        self.assertEquals(config.tonecolors[0], "hi")
        self.assertEquals(len(config.tonecolors), len(Config({}).tonecolors))
    
    def testCopiesInput(self):
        inputSettings = {}
        
        config = Config(inputSettings)
        config.dictlanguage = "foobar"
        
        self.assertEquals(inputSettings, {})
    
    def testDeepCopiesInput(self):
        inputSettings = { "dictlanguage" : [["deep!"]] }
        
        config = Config(inputSettings)
        config.dictlanguage[0][0] = "changed :("
        
        self.assertEquals(inputSettings, { "dictlanguage" : [["deep!"]] })

    def testNoUserSettings(self):
        self.assertNotEquals(Config(None).dictlanguage, None)
    
    def testSupplyDefaultSettings(self):
        self.assertNotEquals(Config({}).dictlanguage, None)
    
    def testDontOverwriteSuppliedSettings(self):
        self.assertEquals(Config({ "dictlanguage" : "foobar" }).dictlanguage, "foobar")
    
    def testPrivateStuffStaysPrivate(self):
        for key in Config({}).settings.keys():
            self.assertFalse("__" in key, "Private stuff called %s leaked" % key)
    
    def testTonified(self):
        self.assertTrue(Config({ "tonedisplay" : "tonified" }).shouldtonify)
        self.assertFalse(Config({ "tonedisplay" : "numeric" }).shouldtonify)
    
    def testNeedMeanings(self):
        def row(mg, dmw, mwag, res):
            self.assertEquals(Config({ "meaninggeneration" : mg, "detectmeasurewords" : dmw, "mwaudiogeneration" : mwag }).needmeanings, res)
        
        row(True, True, True, True)
        row(True, True, False, True)
        row(True, False, True, True)
        row(True, False, False, True)
        row(False, True, True, True)
        row(False, True, False, True)
        row(False, False, True, True)
        row(False, False, False, False)
    
    def testMeaningNumber(self):
        self.assertEquals(map(lambda n: Config({ "meaningnumbering" : "arabicParens", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).meaningnumber(n), [2, 10, 21]),
                          [u"(2)", u"(10)", u"(21)"])
        self.assertEquals(map(lambda n: Config({ "meaningnumbering" : "circledChinese", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).meaningnumber(n), [2, 10, 21]),
                          [u"㊁", u"㊉", u"(21)"])
        self.assertEquals(map(lambda n: Config({ "meaningnumbering" : "circledArabic", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).meaningnumber(n), [2, 10, 21]),
                          [u"②", u"⑩", u"(21)"])
        self.assertEquals(map(lambda n: Config({ "meaningnumbering" : "none", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).meaningnumber(n), [2, 10, 21]),
                          [u"", u"", u""])
        self.assertEquals(map(lambda n: Config({ "meaningnumbering" : "arabicParens", "colormeaningnumbers" : True, "meaningnumberingcolor" : "#aabbcc", "emphasisemainmeaning" : False }).meaningnumber(n), [2, 10, 21]),
                          [u'<span style="color:#aabbcc">(2)</span>', u'<span style="color:#aabbcc">(10)</span>', u'<span style="color:#aabbcc">(21)</span>'])

    def testFormatMeaningsOptions(self):
        self.assertEquals(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "lines", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).formatmeanings([u"a", u"b"]),
                          u"(1) a<br />(2) b")
        self.assertEquals(Config({ "meaningnumbering" : "circledChinese", "meaningseperator" : "commas", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).formatmeanings([u"a", u"b"]),
                          u"㊀ a, ㊁ b")
        self.assertEquals(Config({ "meaningnumbering" : "circledArabic", "meaningseperator" : "custom", "custommeaningseperator" : " | ", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).formatmeanings([u"a", u"b"]),
                          u"① a | ② b")
        self.assertEquals(Config({ "meaningnumbering" : "none", "meaningseperator" : "custom", "custommeaningseperator" : " ^_^ ", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).formatmeanings([u"a", u"b"]),
                          u"a ^_^ b")
        self.assertEquals(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "lines", "colormeaningnumbers" : True, "meaningnumberingcolor" : "#aabbcc", "emphasisemainmeaning" : False }).formatmeanings([u"a", u"b"]),
                        u'<span style="color:#aabbcc">(1)</span> a<br /><span style="color:#aabbcc">(2)</span> b')
    
    def testFormatMeaningsSingleMeaning(self):
        self.assertEquals(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "lines", "emphasisemainmeaning" : False }).formatmeanings([u"a"]), u"a")
    
    def testFormatTooManyMeanings(self):
        self.assertEquals(Config({ "meaningnumbering" : "circledChinese", "meaningseperator" : "commas", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).formatmeanings([str(n) for n in range(1, 22)]),
                          u"㊀ 1, ㊁ 2, ㊂ 3, ㊃ 4, ㊄ 5, ㊅ 6, ㊆ 7, ㊇ 8, ㊈ 9, ㊉ 10, ⑪ 11, ⑫ 12, ⑬ 13, ⑭ 14, ⑮ 15, ⑯ 16, ⑰ 17, ⑱ 18, ⑲ 19, ⑳ 20, (21) 21")

    def testFormatMeaningsWithEmphasis(self):
        self.assertEquals(Config({ "meaningnumbering" : "circledChinese", "meaningseperator" : "commas", "colormeaningnumbers" : False,
                                   "emphasisemainmeaning" : True, "mainmeaningemphasistag" : "br/" }).formatmeanings([u"a", u"b", u"c"]),
                          u"a, <br />㊁ b, ㊂ c")
        self.assertEquals(Config({ "meaningnumbering" : "none", "meaningseperator" : "custom", "custommeaningseperator" : " ^_^ ", "colormeaningnumbers" : False,
                                   "emphasisemainmeaning" : True, "mainmeaningemphasistag" : "small" }).formatmeanings([u"a", u"b", u"c", u"d"]),
                          u"a ^_^ <small>b ^_^ c ^_^ d</small>")
        self.assertEquals(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "lines", "colormeaningnumbers" : True, "meaningnumberingcolor" : "#aabbcc",
                                   "emphasisemainmeaning" : True, "mainmeaningemphasistag" : "mehhh/" }).formatmeanings([u"a", u"b", u"c"]),
                          u'a<br /><mehhh /><span style="color:#aabbcc">(2)</span> b<br /><span style="color:#aabbcc">(3)</span> c')
    
    def testFormatMeaningsWithEmphasisSingleNonMainMeaning(self):
        self.assertEquals(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "commas", "colormeaningnumbers" : False,
                                   "emphasisemainmeaning" : True, "mainmeaningemphasistag" : "br/" }).formatmeanings([u"a", u"b"]),
                          u"a, <br />b")
    
    def testFormatMeaningsWithEmphasisSingleMeaning(self):
        self.assertEquals(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "commas", "colormeaningnumbers" : False,
                                   "emphasisemainmeaning" : True, "mainmeaningemphasistag" : "br/" }).formatmeanings([u"a"]),
                          u"a")

    def testFormatHanziMaskingCharacter(self):
        self.assertEquals(Config({ "hanzimasking" : True, "hanzimaskingcharacter": "MASKED", "colormeaningnumbers" : True, "meaningnumberingcolor" : "#abcdef", "emphasisemainmeaning" : False }).formathanzimaskingcharacter(),
                          u'<span style="color:#abcdef">MASKED</span>')
        self.assertEquals(Config({ "hanzimasking" : True, "hanzimaskingcharacter": "MASKED", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).formathanzimaskingcharacter(),
                          u'MASKED')

    def testShouldUseGoogleTranslateDontUse(self):
        self.assertFalse(Config({ "fallbackongoogletranslate" : False }).shouldusegoogletranslate)
        
    def testShouldUseGoogleTranslateShouldUse(self):
        self.assertTrue(Config({ "fallbackongoogletranslate" : True }).shouldusegoogletranslate)
