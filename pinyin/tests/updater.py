# -*- coding: utf-8 -*-

import copy
import unittest

import pinyin.config
from pinyin.db import database
from pinyin.updater import *
from pinyin.utils import Thunk
from pinyin.mocks import *


englishdict = dictionary.PinyinDictionary.loadall()('en')

class FieldUpdaterFromAudioTest(unittest.TestCase):
    def testDoesntDoAnythingWhenDisabled(self):
        self.assertEquals(self.updatefact(u"hen3 hao3", { "audio" : "", "expression" : "junk" }, forcepinyininaudiotosoundtags = False),
                          { "audio" : "", "expression" : "junk" })
    
    def testWorksIfFieldMissing(self):
        self.assertEquals(self.updatefact(u"hen3 hao3", { "expression" : "junk" }, forcepinyininaudiotosoundtags = True),
                          { "expression" : "junk" })

    def testLeavesOtherFieldsAlone(self):
        self.assertEquals(self.updatefact(u"", { "audio" : "junk", "expression" : "junk" }, forcepinyininaudiotosoundtags = True),
                          { "audio" : u"", "expression" : "junk" })

    def testReformatsAccordingToConfig(self):
        henhaoaudio = u"[sound:" + os.path.join("Test", "hen3.mp3") + "][sound:" + os.path.join("Test", "hao3.mp3") + "]"

        self.assertEquals(
            self.updatefact(u"hen3 hao3", { "audio" : "junky" }, forcepinyininaudiotosoundtags = True),
            { "audio" : henhaoaudio })
        self.assertEquals(
            self.updatefact(u"hen3,hǎo", { "audio" : "junky" }, forcepinyininaudiotosoundtags = True),
            { "audio" : henhaoaudio })
    
    def testDoesntModifySoundTags(self):
        self.assertEquals(
            self.updatefact(u"[sound:aeuth34t0914bnu.mp3][sound:ae390n32uh2ub.mp3]", { "audio" : "" }, forcepinyininaudiotosoundtags = True),
            { "audio" : u"[sound:aeuth34t0914bnu.mp3][sound:ae390n32uh2ub.mp3]" })
        self.assertEquals(
            self.updatefact(u"[sound:hen3.mp3][sound:hao3.mp3]", { "audio" : "" }, forcepinyininaudiotosoundtags = True),
            { "audio" : u"[sound:hen3.mp3][sound:hao3.mp3]" })
    
    # Test helpers
    def updatefact(self, *args, **kwargs):
        infos, fact = self.updatefactwithinfos(*args, **kwargs)
        return fact

    def updatefactwithinfos(self, audio, fact, mediapacks = None, **kwargs):
        notifier = MockNotifier()

        if mediapacks == None:
            mediapacks = [media.MediaPack("Test", { "shu1.mp3" : "shu1.mp3", "shu1.ogg" : "shu1.ogg",
                                                    "san1.mp3" : "san1.mp3", "qi1.ogg" : "qi1.ogg", "Kai1.mp3" : "location/Kai1.mp3",
                                                    "hen3.mp3" : "hen3.mp3", "hen2.mp3" : "hen2.mp3", "hao3.mp3" : "hao3.mp3" })]
        mediamanager = MockMediaManager(mediapacks)

        factclone = copy.deepcopy(fact)
        FieldUpdaterFromAudio(notifier, mediamanager, config.Config(kwargs)).updatefact(factclone, audio)

        return notifier.infos, factclone

class FieldUpdaterFromMeaningTest(unittest.TestCase):
    def testDoesntDoAnythingWhenDisabled(self):
        self.assertEquals(self.updatefact(u"(1) yes (2) no", { "meaning" : "", "expression" : "junk" }, forcemeaningnumberstobeformatted = False),
                          { "meaning" : "", "expression" : "junk" })
    
    def testWorksIfFieldMissing(self):
        self.assertEquals(self.updatefact(u"(1) yes (2) no", { "expression" : "junk" }, forcemeaningnumberstobeformatted = True),
                          { "expression" : "junk" })

    def testLeavesOtherFieldsAlone(self):
        self.assertEquals(self.updatefact(u"", { "meaning" : "junk", "expression" : "junk" }, forcemeaningnumberstobeformatted = True),
                          { "meaning" : u"", "expression" : "junk" })

    def testReformatsAccordingToConfig(self):
        self.assertEquals(
            self.updatefact(u"(1) yes (2) no", { "meaning" : "junky" },
                forcemeaningnumberstobeformatted = True, meaningnumbering = "circledArabic", colormeaningnumbers = False),
                { "meaning" : u"① yes ② no" })
        self.assertEquals(
            self.updatefact(u"(10) yes 2 no", { "meaning" : "junky" },
                forcemeaningnumberstobeformatted = True, meaningnumbering = "none", colormeaningnumbers = False),
                { "meaning" : u" yes 2 no" })
    
    # Test helpers
    def updatefact(self, reading, fact, **kwargs):
        factclone = copy.deepcopy(fact)
        FieldUpdaterFromMeaning(config.Config(kwargs)).updatefact(factclone, reading)
        return factclone

class FieldUpdaterFromReadingTest(unittest.TestCase):
    def testDoesntDoAnythingWhenDisabled(self):
        self.assertEquals(self.updatefact(u"hen3 hǎo", { "reading" : "", "expression" : "junk" }, forcereadingtobeformatted = False),
                          { "reading" : "", "expression" : "junk" })
    
    def testDoesSomethingWhenDisabledIfAlways(self):
        fact = { "reading" : "", "expression" : "junk" }
        FieldUpdaterFromReading(config.Config({ "forcereadingtobeformatted" : False })).updatefactalways(fact, u"also junk")
        self.assertEquals(fact, { "reading" : "also junk", "expression" : "junk" })
    
    def testWorksIfFieldMissing(self):
        self.assertEquals(self.updatefact(u"hen3 hǎo", { "expression" : "junk" }, forcereadingtobeformatted = True),
                          { "expression" : "junk" })

    def testLeavesOtherFieldsAlone(self):
        self.assertEquals(self.updatefact(u"", { "reading" : "junk", "expression" : "junk" }, forcereadingtobeformatted = True),
                          { "reading" : u"", "expression" : "junk" })

    def testReformatsAccordingToConfig(self):
        self.assertEquals(
            self.updatefact(u"hen3 hǎo", { "reading" : "junky" },
                forcereadingtobeformatted = True, tonedisplay = "tonified",
                colorizedpinyingeneration = True, tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"]),
                { "reading" : u'<span style="color:#333333">hěn</span> <span style="color:#333333">hǎo</span>' })
    
    def testReformattingRespectsExistingColorization(self):
        self.assertEquals(
            self.updatefact(u"<span style='color: red'>hen3</span> hǎo", { "reading" : "junky" },
                forcereadingtobeformatted = True, tonedisplay = "numeric",
                colorizedpinyingeneration = True, tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"]),
                { "reading" : u'<span style=\"\"><span style="color: red">hen3</span></span> <span style="color:#333333">hao3</span>' })

    # Test helpers
    def updatefact(self, reading, fact, **kwargs):
        factclone = copy.deepcopy(fact)
        FieldUpdaterFromReading(config.Config(kwargs)).updatefact(factclone, reading)
        return factclone

class FieldUpdaterFromExpressionTest(unittest.TestCase):
    def testAutoBlanking(self):
        self.assertEquals(self.updatefact(u"", { "reading" : "blather", "meaning" : "junk", "color" : "yes!", "trad" : "meh", "simp" : "yay" }),
                          { "reading" : "", "meaning" : "", "color" : "", "trad" : "", "simp" : "" })
    
    def testAutoBlankingAudioMeasureWord(self):
        # TODO: test behaviour for audio and measure word, once we know what it should be
        pass
    
    def testFullUpdate(self):
        self.assertEquals(
            self.updatefact(u"书", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "trad" : "", "simp" : "" },
                colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True, emphasisemainmeaning = False,
                tonedisplay = "tonified", meaningnumbering = "circledChinese", colormeaningnumbers = False, meaningseperator = "lines", prefersimptrad = "simp",
                audiogeneration = True, audioextensions = [".mp3"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], weblinkgeneration = False, hanzimasking = False,
                tradgeneration = True, simpgeneration = True, forceexpressiontobesimptrad = False), {
                    "reading" : u'<span style="color:#ff0000">shū</span>',
                    "meaning" : u'㊀ book<br />㊁ letter<br />㊂ see also <span style="color:#ff0000">\u4e66</span><span style="color:#ff0000">\u7ecf</span> Book of History',
                    "mw" : u'<span style="color:#00aa00">本</span> - <span style="color:#00aa00">běn</span>, <span style="color:#0000ff">册</span> - <span style="color:#0000ff">cè</span>, <span style="color:#0000ff">部</span> - <span style="color:#0000ff">bù</span>',
                    "audio" : u"[sound:" + os.path.join("Test", "shu1.mp3") + "]",
                    "color" : u'<span style="color:#ff0000">书</span>',
                    "trad" : u"書", "simp" : u"书"
                  })
    
    def testFullUpdateGerman(self):
        self.assertEquals(
            self.updatefact(u"书", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "trad" : "", "simp" : "" },
                dictlanguage = "de",
                colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True,
                tonedisplay = "tonified", audiogeneration = True, audioextensions = [".ogg"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"],
                tradgeneration = True, simpgeneration = True, forceexpressiontobesimptrad = False), {
                    "reading" : u'<span style="color:#ff0000">shū</span>',
                    "meaning" : u'Buch, Geschriebenes (S)',
                    "mw" : u'',
                    "audio" : u"[sound:" + os.path.join("Test", "shu1.ogg") + "]",
                    "color" : u'<span style="color:#ff0000">书</span>',
                    "trad" : u"書", "simp" : u"书"
                  })
    
    def testUpdatePreservesWhitespace(self):
        self.assertEquals(
            self.updatefact(u"\t书", { "reading" : "", "color" : "", "trad" : "", "simp" : "" },
                dictlanguage = "en",
                colorizedpinyingeneration = False, colorizedcharactergeneration = True, meaninggeneration = False,
                tonedisplay = "tonified", audiogeneration = False, tradgeneration = True, simpgeneration = True, forceexpressiontobesimptrad = False), {
                    "reading" : u'\tshū',
                    "color" : u'\t<span style="color:#ff0000">书</span>',
                    # TODO: make the simp and trad fields preserve whitespace more reliably by moving away
                    # from Google Translate as the translator. Currently this flips between preserving and
                    # not preserving seemingly nondeterministically!
                    "trad" : u"書", "simp" : u"书"
                  })
    
    def testDontOverwriteFields(self):
        self.assertEquals(
            self.updatefact(u"书", { "reading" : "a", "meaning" : "b", "mw" : "c", "audio" : "d", "color" : "e", "trad" : "f", "simp" : "g" },
                colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True,
                tonedisplay = "tonified", meaningnumbering = "circledChinese", meaningseperator = "lines", prefersimptrad = "simp",
                audiogeneration = True, audioextensions = [".mp3"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], weblinkgeneration = True,
                tradgeneration = True, simpgeneration = True), {
                    "reading" : "a", "meaning" : "b", "mw" : "c", "audio" : "d", "color" : "e", "trad" : "f", "simp" : "g"
                  })
    
    def testUpdateExpressionItself(self):
        self.assertEquals(
            self.updatefact(u"啤酒", { "expression" : "" },
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False,
                detectmeasurewords = False, audiogeneration = False, weblinkgeneration = False), { "expression" : u"啤酒" })
    
    def testUpdateMeaningAndMWWithoutMWField(self):
        self.assertEquals(
            self.updatefact(u"啤酒", { "expression" : "", "meaning" : "" },
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = True, emphasisemainmeaning = False,
                meaningnumbering = "circledChinese", colormeaningnumbers = False, detectmeasurewords = True, audiogeneration = False, weblinkgeneration = False,
                forceexpressiontobesimptrad = False), {
                    "expression" : u"啤酒", "meaning" : u"㊀ beer<br />㊁ MW: 杯 - b\u0113i, 瓶 - p\xedng, 罐 - gu\xe0n, 桶 - t\u01d2ng, 缸 - g\u0101ng"
                  })

    def testMeaningHanziMasking(self):
        self.assertEquals(
            self.updatefact(u"书", { "meaning" : "" },
                colorizedpinyingeneration = True, colorizedcharactergeneration = False, meaninggeneration = True, detectmeasurewords = False, emphasisemainmeaning = False,
                tonedisplay = "tonified", meaningnumbering = "circledArabic", colormeaningnumbers = True, meaningnumberingcolor="#123456", meaningseperator = "custom", custommeaningseperator = " | ", prefersimptrad = "simp",
                audiogeneration = True, audioextensions = [".mp3"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], weblinkgeneration = False, hanzimasking = True, hanzimaskingcharacter = "MASKED"), {
                    "meaning" : u'<span style="color:#123456">①</span> book | <span style="color:#123456">②</span> letter | <span style="color:#123456">③</span> see also <span style="color:#123456">MASKED</span><span style="color:#ff0000">\u7ecf</span> Book of History | <span style="color:#123456">④</span> MW: <span style="color:#00aa00">本</span> - <span style="color:#00aa00">běn</span>, <span style="color:#0000ff">册</span> - <span style="color:#0000ff">cè</span>, <span style="color:#0000ff">部</span> - <span style="color:#0000ff">bù</span>',
                  })

    def testMeaningSurnameMasking(self):
        self.assertEquals(
            self.updatefact(u"汪", { "meaning" : "" },
                meaninggeneration = True, meaningnumbering = "arabicParens", colormeaningnumbers = False, meaningseperator = "lines", emphasisemainmeaning = False), {
                    "meaning" : u'(1) expanse of water<br />(2) ooze<br />(3) (a surname)',
                  })

    def testMeaningChineseNumbers(self):
        self.assertEquals(self.updatefact(u"九千零二十五", { "meaning" : "" }, meaninggeneration = True), { "meaning" : u'9025' })

    def testMeaningWesternNumbersYear(self):
        self.assertEquals(self.updatefact(u"2001年", { "meaning" : "" }, meaninggeneration = True), { "meaning" : u'2001AD' })

    def testUpdateReadingOnly(self):
        self.assertEquals(
            self.updatefact(u"啤酒", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False,
                detectmeasurewords = False, audiogeneration = False, tonedisplay = "numeric", weblinkgeneration = False), {
                    "reading" : u'pi2 jiu3', "meaning" : "", "mw" : "", "audio" : "", "color" : ""
                  })
    
    def testUpdateReadingAndMeaning(self):
        self.assertEquals(
            self.updatefact(u"㝵", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : "" },
                colorizedpinyingeneration = True, colorizedcharactergeneration = False, meaninggeneration = True, detectmeasurewords = False, tonedisplay = "numeric", emphasisemainmeaning = False,
                meaningnumbering = "arabicParens", colormeaningnumbers = True, meaningnumberingcolor = "#123456", meaningseperator = "commas", prefersimptrad = "trad",
                audiogeneration = False, tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], weblinkgeneration = False), {
                    "reading" : u'<span style="color:#ffaa00">de2</span>',
                    "meaning" : u'<span style="color:#123456">(1)</span> to obtain, <span style="color:#123456">(2)</span> archaic variant of <span style="color:#ffaa00">得</span> - <span style="color:#ffaa00">de2</span>, <span style="color:#123456">(3)</span> component in <span style="color:#0000ff">礙</span> - <span style="color:#0000ff">ai4</span> and <span style="color:#ffaa00">鍀</span> - <span style="color:#ffaa00">de2</span>',
                    "mw" : "", "audio" : "", "color" : "", "weblinks" : ""
                  })
    
    def testUpdateReadingAndMeasureWord(self):
        self.assertEquals(
            self.updatefact(u"丈夫", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : "" },
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = True,
                tonedisplay = "numeric", prefersimptrad = "trad", audiogeneration = False, weblinkgeneration = False), {
                    "reading" : u'zhang4 fu', "meaning" : u'',
                    "mw" : u"個 - ge4", "audio" : "", "color" : "", "weblinks" : ""
                  })
    
    def testUpdateReadingAndAudio(self):
        self.assertEquals(
            self.updatefact(u"三七開", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : "" },
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = False,
                tonedisplay = "tonified", audiogeneration = True, audioextensions = [".mp3", ".ogg"], weblinkgeneration = False), {
                    "reading" : u'sān qī kāi', "meaning" : u'', "mw" : "",
                    "audio" : u"[sound:" + os.path.join("Test", "san1.mp3") + "]" +
                              u"[sound:" + os.path.join("Test", "qi1.ogg") + "]" +
                              u"[sound:" + os.path.join("Test", "location/Kai1.mp3") + "]",
                    "color" : "", "weblinks" : ""
                  })
    
    def testUpdateReadingAndColoredHanzi(self):
        self.assertEquals(
            self.updatefact(u"三峽水库", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : u"" },
                dictlanguage = "pinyin", colorizedpinyingeneration = False, colorizedcharactergeneration = True, meaninggeneration = False, detectmeasurewords = False,
                tonedisplay = "numeric", audiogeneration = False, tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"], weblinkgeneration = False), {
                    "reading" : u'san1 xia2 shui3 ku4', "meaning" : u'', "mw" : "", "audio" : "",
                    "color" : u'<span style="color:#111111">三</span><span style="color:#222222">峽</span><span style="color:#333333">水</span><span style="color:#444444">库</span>', "weblinks" : ""
                  })
    
    def testUpdateReadingAndLinks(self):
        self.assertEquals(
            self.updatefact(u"一概", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : "Yes, I get overwritten!" },
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = False,
                tonedisplay = "numeric", audiogeneration = False, tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"],
                weblinkgeneration = True, weblinks = [("YEAH!", "mytitle", "silly{searchTerms}url"), ("NAY!", "myothertitle", "verysilly{searchTerms}url")]), {
                    "reading" : u'yi1 gai4', "meaning" : u'', "mw" : "", "audio" : "", "color" : u'',
                    "weblinks" : u'[<a href="silly%E4%B8%80%E6%A6%82url" title="mytitle">YEAH!</a>] [<a href="verysilly%E4%B8%80%E6%A6%82url" title="myothertitle">NAY!</a>]'
                  })

    def testWebLinkFieldCanBeMissingAndStaysMissing(self):
        self.assertEquals(self.updatefact(u"一概", { }, weblinkgeneration = True), { })
    
    def testWebLinksNotBlankedIfDisabled(self):
        self.assertEquals(self.updatefact(u"一概", { "weblinks": "Nope!" }, weblinkgeneration = False), { "weblinks" : "Nope!" })
    
    def testReadingFromWesternNumbers(self):
        self.assertEquals(self.updatefact(u"111", { "reading" : "" }, colorizedpinyingeneration = True, tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"]),
                                                  { "reading" : u'<span style="color:#333333">b\u01cei</span> <span style="color:#111111">y\u012b</span> <span style="color:#222222">sh\xed</span> <span style="color:#111111">y\u012b</span>' })
    
    def testNotifiedUponAudioGenerationWithNoPacks(self):
        infos, fact = self.updatefactwithinfos(u"三月", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                            mediapacks = [],
                            colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = False,
                            tonedisplay = "numeric", audiogeneration = True)
        
        self.assertEquals(fact, { "reading" : u'san1 yue4', "meaning" : u'', "mw" : "", "audio" : "", "color" : "" })
        self.assertEquals(len(infos), 1)
        self.assertTrue("cannot" in infos[0])
    
    def testUpdateMeasureWordAudio(self):
        quantitydigitpinyin = ["yi1", "liang3", "liang2", "san1", "si4", "wu3", "wu2", "liu4", "qi1", "ba1", "jiu3", "jiu2", "ji3", "ji2"]
        allpinyin = quantitydigitpinyin + ["pi2", "bei1", "ping2", "guan4", "tong3", "tong2", "gang1"]
        
        pack = media.MediaPack("MWAudio", dict([(pinyin + ".mp3", pinyin + ".mp3") for pinyin in allpinyin]))
        
        # NB: turning off meaninggeneration here triggers a bug that happened in 0.6 where
        # we wouldn't set up the dictmeasurewords for the mwaudio
        mwaudio = self.updatefact(u"啤酒", { "mwaudio" : "" }, meaninggeneration = False, detectmeasurewords = False, mwaudiogeneration = True, audioextensions = [".mp3", ".ogg"], mediapacks = [pack])["mwaudio"]
        for quantitydigit in quantitydigitpinyin:
            mwaudio = mwaudio.replace(quantitydigit, "X")
        
        # jiu3 in the numbers aliases with jiu3 in the characters :(
        sounds = ["X", "bei1", "pi2", "X",
                  "X", "ping2", "pi2", "X",
                  "X", "guan4", "pi2", "X",
                  "X", "tong3", "pi2", "X",
                  "X", "gang1", "pi2", "X"]
        self.assertEquals(mwaudio, "".join([u"[sound:" + os.path.join("MWAudio", sound + ".mp3") + "]" for sound in sounds]))

    def testFallBackOnGoogleForPhrase(self):
        self.assertEquals(
            self.updatefact(u"你好，你是我的朋友吗", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                fallbackongoogletranslate = True,
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = True, detectmeasurewords = False,
                tonedisplay = "numeric", audiogeneration = False, hanzimasking = False), {
                    "reading" : u'ni3 hao3, ni3 shi4 wo3 de peng2 you ma',
                    "meaning" : u'Hello, you are my friend do<br /><span style="color:gray"><small>[Google Translate]</small></span><span> </span>',
                    "mw" : "", "audio" : "", "color" : ""
                  })

    def testUpdateSimplifiedTraditional(self):
        self.assertEquals(
            self.updatefact(u"个個", { "simp" : "", "trad" : "" },
                simpgeneration = True, tradgeneration = True), {
                    "simp"  : u"个个",
                    "trad" : u"個個"
                  })

    def testUpdateSimplifiedTraditionalDoesNothingIfSimpTradIdentical(self):
        self.assertEquals(
            self.updatefact(u"鼠", { "simp" : "", "trad" : "" }, simpgeneration = True, tradgeneration = True), { "simp"  : u"", "trad" : u"" })

    def testOverwriteExpressionWithSimpTrad(self):
        self.assertEquals(self.updatefact(u"个個", { "expression" : "" }, forceexpressiontobesimptrad = True, prefersimptrad = "trad"),
                                                 { "expression"  : u"個個" })

        self.assertEquals(self.updatefact(u"个個", { "expression" : "" }, forceexpressiontobesimptrad = True, prefersimptrad = "simp"),
                                                 { "expression"  : u"个个" })

    def testOverwriteExpressionWithSimpTradEvenWorksIfFieldFilled(self):
        self.assertEquals(self.updatefact(u"个個", { "expression" : "I'm Filled!" }, forceexpressiontobesimptrad = True, prefersimptrad = "trad"),
                                                 { "expression"  : u"個個" })

    def testOverwriteExpressionWithSimpTradCausesColoredCharsToUpdateEvenIfFilled(self):
        self.assertEquals(
            self.updatefact(u"个個", { "expression" : "I'm Filled!", "color" : "dummy" },
                            forceexpressiontobesimptrad = True, prefersimptrad = "trad", tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"]),
                            { "expression"  : u"個個", "color" : u'<span style="color:#444444">個</span><span style="color:#444444">個</span>' })

    def testDontOverwriteFilledColoredCharactersIfSimpTradDoesntChange(self):
        self.assertEquals(
            self.updatefact(u"個個", { "expression" : "I'm Filled!", "color" : "dummy" },
                            forceexpressiontobesimptrad = True, prefersimptrad = "trad", tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"]),
                            { "expression"  : u"個個", "color" : "dummy" })

    def testUpdateReadingAndColoredHanziAndAudioWithSandhi(self):
        self.assertEquals(
            self.updatefact(u"很好", { "reading" : "", "color" : "", "audio" : "" },
                colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = False,
                detectmeasurewords = False, audiogeneration = True, audioextensions = [".mp3"], tonedisplay = "numeric",
                tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], weblinkgeneration = False), {
                    "reading" : u'<span style="color:#66cc66">hen3</span> <span style="color:#00aa00">hao3</span>',
                    "color" : u'<span style="color:#66cc66">很</span><span style="color:#00aa00">好</span>',
                    "audio" : u"[sound:" + os.path.join("Test", "hen2.mp3") + "]" +
                              u"[sound:" + os.path.join("Test", "hao3.mp3") + "]"
                  })
    
    # Test helpers
    def updatefact(self, *args, **kwargs):
        infos, fact = self.updatefactwithinfos(*args, **kwargs)
        return fact
    
    def updatefactwithinfos(self, expression, fact, mediapacks = None, **kwargs):
        notifier = MockNotifier()
        
        if mediapacks == None:
            mediapacks = [media.MediaPack("Test", { "shu1.mp3" : "shu1.mp3", "shu1.ogg" : "shu1.ogg",
                                                    "san1.mp3" : "san1.mp3", "qi1.ogg" : "qi1.ogg", "Kai1.mp3" : "location/Kai1.mp3",
                                                    "hen3.mp3" : "hen3.mp3", "hen2.mp3" : "hen2.mp3", "hao3.mp3" : "hao3.mp3" })]
        mediamanager = MockMediaManager(mediapacks)
        
        factclone = copy.deepcopy(fact)
        FieldUpdaterFromExpression(notifier, mediamanager, config.Config(utils.updated({ "dictlanguage" : "en" }, kwargs))).updatefact(factclone, expression)
        
        return notifier.infos, factclone