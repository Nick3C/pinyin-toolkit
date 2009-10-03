# -*- coding: utf-8 -*-

import copy
import unittest

import pinyin.config
from pinyin.db import database
from pinyin.updater import *
from pinyin.utils import Thunk
from pinyin.mocks import *


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
                    "meaning" : u'㊀ book<br />㊁ letter<br />㊂ same as <span style="color:#ff0000">\u4e66</span><span style="color:#ff0000">\u7ecf</span> Book of History',
                    "mw" : u'<span style="color:#00aa00">本</span> - <span style="color:#00aa00">běn</span>, <span style="color:#0000ff">册</span> - <span style="color:#0000ff">cè</span>, <span style="color:#0000ff">部</span> - <span style="color:#0000ff">bù</span>, <span style="color:#ffaa00">丛</span> - <span style="color:#ffaa00">cóng</span>',
                    "audio" : u"[sound:" + os.path.join("Test", "shu1.mp3") + "]",
                    "color" : u'<span style="color:#ff0000">书</span>',
                    "trad" : u"書", "simp" : u"书"
                  })
    
    def testDontOverwriteFields(self):
        self.assertEquals(
            self.updatefact(u"书", { "reading" : "a", "meaning" : "b", "mw" : "c", "audio" : "[sound:foo.mp3]", "color" : "e", "trad" : "f", "simp" : "g" },
                colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True,
                tonedisplay = "tonified", meaningnumbering = "circledChinese", meaningseperator = "lines", prefersimptrad = "simp",
                audiogeneration = True, audioextensions = [".mp3"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], weblinkgeneration = True,
                tradgeneration = True, simpgeneration = True), {
                    "reading" : "a", "meaning" : "b", "mw" : "c", "audio" : "[sound:foo.mp3]", "color" : "e", "trad" : "f", "simp" : "g"
                  })
    
    def testUpdateExpressionItself(self):
        self.assertEquals(self.updatefact(u"啤酒", { "expression" : "" }), { "expression" : u"啤酒" })

    def testWebLinkFieldCanBeMissingAndStaysMissing(self):
        self.assertEquals(self.updatefact(u"一概", { }, weblinkgeneration = True), { })
    
    def testWebLinksNotBlankedIfDisabled(self):
        self.assertEquals(self.updatefact(u"一概", { "weblinks": "Nope!" }, weblinkgeneration = False), { "weblinks" : "Nope!" })
    
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