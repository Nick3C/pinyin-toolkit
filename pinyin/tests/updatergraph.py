# -*- coding: utf-8 -*-

import copy
import unittest

import pinyin.config
from pinyin.db import database
from pinyin.updatergraph import *
import pinyin.utils
from pinyin.mocks import *


def adict(**kwargs):
    return kwargs

class UpdaterGraphTest(unittest.TestCase):
    def testEverythingEnglish(self):
        config = adict(prefersimptrad = "simp", forceexpressiontobesimptrad = False, tonedisplay = "tonified", hanzimasking = False,
                        emphasisemainmeaning = False, meaningnumbering = "circledChinese", colormeaningnumbers = False, meaningseperator = "lines",
                        audioextensions = [".mp3"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"])
        self.assertProduces({ "expression" : u"书", "mwfieldinfact" : True }, config, {
            "reading" : u'<span style="color:#ff0000">shū</span>',
            "meaning" : u'㊀ book<br />㊁ letter<br />㊂ same as <span style="color:#ff0000">\u4e66</span><span style="color:#ff0000">\u7ecf</span> Book of History',
            "mw" : u'<span style="color:#00aa00">本</span> - <span style="color:#00aa00">běn</span>, <span style="color:#0000ff">册</span> - <span style="color:#0000ff">cè</span>, <span style="color:#0000ff">部</span> - <span style="color:#0000ff">bù</span>, <span style="color:#ffaa00">丛</span> - <span style="color:#ffaa00">cóng</span>',
            "audio" : u"[sound:" + os.path.join("Test", "shu1.mp3") + "]",
            "color" : u'<span style="color:#ff0000">书</span>',
            "trad" : u"書", "simp" : u"书"
          })

    def testEverythingGerman(self):
        config = adict(forceexpressiontobesimptrad = False, tonedisplay = "tonified",
                       dictlanguage = "de", detectmeasurewords = True,
                       audioextensions = [".ogg"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"])
        self.assertProduces({ "expression" : u"书", "mwfieldinfact" : True }, config, {
            "reading" : u'<span style="color:#ff0000">shū</span>',
            "meaning" : u'Buch, Geschriebenes (S)',
            "mw" : u'',
            "audio" : u"[sound:" + os.path.join("Test", "shu1.ogg") + "]",
            "color" : u'<span style="color:#ff0000">书</span>',
            "trad" : u"書", "simp" : u"书"
          })  

    def testPreservesWhitespace(self):
        config = adict(forceexpressiontobesimptrad = False, tonedisplay = "tonified", colorizedpinyingeneration = False)
        self.assertProduces({ "expression" : u"\t书" }, config, {
            "reading" : u'\tshū',
            "color" : u'\t<span style="color:#ff0000">书</span>',
            # TODO: make the simp and trad fields preserve whitespace more reliably by moving away
            # from Google Translate as the translator
            "trad" : u"\t書", "simp" : u"\t书"
          })

    def testUpdateMeaningAndMWWithoutMWField(self):
        config = adict(forceexpressiontobesimptrad = False, colorizedpinyingeneration = False, emphasisemainmeaning = False,
                       meaningnumbering = "circledChinese", colormeaningnumbers = False, detectmeasurewords = True)
        self.assertProduces({ "expression" : u"啤酒", "mwfieldinfact" : False }, config, {
            "expression" : u"啤酒",
            "meaning" : u"㊀ beer<br />㊁ MW: 杯 - b\u0113i, 瓶 - p\xedng, 罐 - gu\xe0n, 桶 - t\u01d2ng, 缸 - g\u0101ng"
          })

    def testMeaningHanziMasking(self):
        config = adict(colorizedpinyingeneration = True, detectmeasurewords = False, emphasisemainmeaning = False,
                       tonedisplay = "tonified", meaningnumbering = "circledArabic", colormeaningnumbers = True, meaningnumberingcolor="#123456", meaningseperator = "custom", custommeaningseperator = " | ", prefersimptrad = "simp",
                       tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], hanzimasking = True, hanzimaskingcharacter = "MASKED")
        self.assertProduces({ "expression" : u"书", "mwfieldinfact" : False }, config, {
            "meaning" : u'<span style="color:#123456">①</span> book | <span style="color:#123456">②</span> letter | <span style="color:#123456">③</span> same as <span style="color:#123456">MASKED</span><span style="color:#ff0000">\u7ecf</span> Book of History | <span style="color:#123456">④</span> MW: <span style="color:#00aa00">本</span> - <span style="color:#00aa00">běn</span>, <span style="color:#0000ff">册</span> - <span style="color:#0000ff">cè</span>, <span style="color:#0000ff">部</span> - <span style="color:#0000ff">bù</span>, <span style="color:#ffaa00">丛</span> - <span style="color:#ffaa00">cóng</span>',
          })

    def testMeaningSurnameMasking(self):
        config = adict(meaningnumbering = "arabicParens", colormeaningnumbers = False, meaningseperator = "lines", emphasisemainmeaning = False)
        self.assertProduces({ "expression" : u"汪", "mwfieldinfact" : False }, config, {
            "meaning" : u'(1) expanse of water<br />(2) ooze<br />(3) (a surname)',
          })

    def testMeaningChineseNumbers(self):
        self.assertProduces({ "expression" : u"九千零二十五", "mwfieldinfact" : False }, {}, { "meaning" : u'9025' })

    def testMeaningWesternNumbersYear(self):
        self.assertProduces({ "expression" : u"2001年", "mwfieldinfact" : False }, {}, { "meaning" : u'2001AD' })

    def assertProduces(self, known, configdict, expected, mediapacks=None):
        if mediapacks == None:
            mediapacks = [media.MediaPack("Test", { "shu1.mp3" : "shu1.mp3", "shu1.ogg" : "shu1.ogg",
                                                    "san1.mp3" : "san1.mp3", "qi1.ogg" : "qi1.ogg", "Kai1.mp3" : "location/Kai1.mp3",
                                                    "hen3.mp3" : "hen3.mp3", "hen2.mp3" : "hen2.mp3", "hao3.mp3" : "hao3.mp3" })]
        
        gbu = GraphBasedUpdater(MockNotifier(), MockMediaManager(mediapacks), pinyin.config.Config(pinyin.utils.updated({ "dictlanguage" : "en" }, configdict)))
        actual = gbu.fillneeded(known, expected.keys())
        
        # Broken down assertion checks here for ease of debugging when they go wrong
        self.assertEquals(sorted(actual.keys()), sorted(expected.keys()))
        for key, value in actual.items():
            self.assertEquals(value, expected[key])
