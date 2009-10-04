# -*- coding: utf-8 -*-

import copy
import unittest
from testutils import *

import pinyin.config
from pinyin.db import database
from pinyin.factproxy import markgeneratedfield, isgeneratedfield
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

class TestFieldUpdaterFromExpression(object):
    def testAutoBlankingGenerated(self):
        self.assertUpdatesTo(u"", {}, {
              "reading" : markgeneratedfield("blather"),
              "meaning" : markgeneratedfield("junk"), 
              "color" : markgeneratedfield("yes!"), 
              "trad" : markgeneratedfield("meh"), 
              "simp" : markgeneratedfield("yay"), 
              "audio" : markgeneratedfield("moo"), 
              "mwaudio" : markgeneratedfield("mehh"), 
              "mw" : markgeneratedfield("a mw")
            },
            { "reading" : "", "meaning" : "", "color" : "", "trad" : "", "simp" : "", "audio" : "", "mwaudio" : "", "mw" : "" })
    
    def testDosentAutoBlankNonGenerated(self):
        nonempty = { "reading" : "a", "meaning" : "b", "color" : "c", "trad" : "d", "simp" : "e", "audio" : "f", "mwaudio" : "g", "mw" : "h" }
        self.assertUpdatesTo(u"", {}, nonempty, nonempty)
    
    def testGenerateAllFieldsWhenEmptyOrGenerated(self):
        config = dict(colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True, emphasisemainmeaning = False,
                      tonedisplay = "tonified", meaningnumbering = "circledChinese", colormeaningnumbers = False, meaningseperator = "lines", prefersimptrad = "simp",
                      audiogeneration = True, mwaudiogeneration = True, audioextensions = [".mp3"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], weblinkgeneration = False, hanzimasking = False,
                      tradgeneration = True, simpgeneration = True, forceexpressiontobesimptrad = False)
        
        for default in ["", markgeneratedfield("Generated")]:
            expected = {
                "expression" : u"书",
                "reading" : markgeneratedfield(u'<span style="color:#ff0000">shū</span>'),
                "meaning" : markgeneratedfield(u'㊀ book<br />㊁ letter<br />㊂ same as <span style="color:#ff0000">\u4e66</span><span style="color:#ff0000">\u7ecf</span> Book of History'),
                "mw" : markgeneratedfield(u'<span style="color:#00aa00">本</span> - <span style="color:#00aa00">běn</span>, <span style="color:#0000ff">册</span> - <span style="color:#0000ff">cè</span>, <span style="color:#0000ff">部</span> - <span style="color:#0000ff">bù</span>, <span style="color:#ffaa00">丛</span> - <span style="color:#ffaa00">cóng</span>'),
                "audio" : markgeneratedfield(u"[sound:" + os.path.join("Test", "shu1.mp3") + "]"),
                "mwaudio" : lambda mwaudio: assert_equal(sanitizequantitydigits(mwaudio), markgeneratedfield((u"[sound:" + os.path.join("Test", "X.mp3") + u"][sound:" + os.path.join("Test", "shu1.mp3") + "]") * 4)),
                "color" : markgeneratedfield(u'<span style="color:#ff0000">书</span>'),
                "trad" : markgeneratedfield(u"書"),
                "simp" : markgeneratedfield(u"书")
              }
            yield self.assertUpdatesTo, u"书", config, { "reading" : default, "meaning" : default, "mw" : default, "audio" : default, "mwaudio" : default, "color" : default, "trad" : default, "simp" : default }, expected
    
    def testDontOverwriteNonGeneratedFields(self):
        config = dict(colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True,
                      tonedisplay = "tonified", meaningnumbering = "circledChinese", meaningseperator = "lines", prefersimptrad = "simp",
                      audiogeneration = True, mwaudiogeneration = True, audioextensions = [".mp3"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], weblinkgeneration = True,
                      tradgeneration = True, simpgeneration = True)
        self.assertUpdatesTo(u"书", config,
            { "expression" : "", "reading" : "a", "meaning" : "b", "mw" : "c", "audio" : "[sound:foo.mp3]", "mwaudio" : "[sound:foo.mp3]", "color" : "e", "trad" : "f", "simp" : "g" },
            { "expression" : u"书", "reading" : "a", "meaning" : "b", "mw" : "c", "audio" : "[sound:foo.mp3]", "mwaudio" : "[sound:foo.mp3]", "color" : "e", "trad" : "f", "simp" : "g" })
    
    def testUpdateControlFlags(self):
        baseconfig = dict(readinggeneration = False, colorizedpinyingeneration = True, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = False,
                          audiogeneration = False, mwaudiogeneration = False, weblinkgeneration = False, tradgeneration = False, simpgeneration = False, forceexpressiontobesimptrad = False)
        blank = { "expression" : u"书", "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "mwaudio" : "", "color" : "", "trad" : "", "simp" : "" }
        for field, flag in config.updatecontrolflags.items():
            if flag is None or field == 'weblinks':
                continue
            
            expected = utils.updated(dict(**blank), { field : lambda s, field=field: assert_true(isgeneratedfield(field, s) and len(s) > 0) })
            yield self.assertUpdatesTo, u"书", utils.updated(dict(**baseconfig), { flag : True }), blank, expected
    
    def testUpdateExpressionItself(self):
        self.assertUpdatesTo(u"啤酒", {}, { "expression" : "" }, { "expression" : u"啤酒" })
        self.assertUpdatesTo(u"啤酒", {}, { "expression" : "Filled" }, { "expression" : u"啤酒" })

    def testWebLinkFieldCanBeMissingAndStaysMissing(self):
        config = dict(weblinkgeneration = True)
        self.assertUpdatesTo(u"一概", config, { "expression" : "" }, { "expression" : u"一概" })
    
    def testWebLinksNotBlankedIfDisabled(self):
        config = dict(weblinkgeneration = False)
        self.assertUpdatesTo(u"一概", config, { "expression" : "", "weblinks": "Nope!" }, { "expression" : u"一概", "weblinks" : "Nope!" })
    
    def testRefomatExpressionAsSimpTrad(self):
        self.assertUpdatesTo(u"个個", dict(forceexpressiontobesimptrad = True, prefersimptrad = "trad"), { "expression" : u"个個" }, { "expression"  : u"個個" })
        self.assertUpdatesTo(u"个個", dict(forceexpressiontobesimptrad = True, prefersimptrad = "simp"), { "expression" : u"个個" }, { "expression"  : u"个个" })

    # Test helpers
    def assertUpdatesTo(self, expression, theconfig, incomingfact, expectedfact, extraaudio=None):
        mediapacks = [media.MediaPack("Test", utils.updated(
                        { "shu1.mp3" : "shu1.mp3", "shu1.ogg" : "shu1.ogg", "san1.mp3" : "san1.mp3", "qi1.ogg" : "qi1.ogg",
                          "Kai1.mp3" : "location/Kai1.mp3", "hen3.mp3" : "hen3.mp3", "hen2.mp3" : "hen2.mp3", "hao3.mp3" : "hao3.mp3" }, quantitydigitmediadict))]
        actualfact = copy.deepcopy(incomingfact)
        FieldUpdaterFromExpression(MockNotifier(), MockMediaManager(mediapacks), config.Config(utils.updated({ "dictlanguage" : "en" }, theconfig))).updatefact(actualfact, expression)
        assert_dict_equal(actualfact, expectedfact, values_as_assertions=True)
