# -*- coding: utf-8 -*-

import copy
import unittest
from testutils import *

import pinyin.config
from pinyin.db import database
from pinyin.factproxy import markgeneratedfield
from pinyin.updatergraph import *
import pinyin.utils
from pinyin.mocks import *


class TestUpdaterGraphGeneralFunctionality(object):
    def testDoesntUpdateNonGeneratedFields(self):
        updaters = [
            ("output", lambda _: "modified output", ("input",))
          ]
        
        graph = filledgraphforupdaters(updaters, { "input" : "hello", "output" : "original output" }, { "input" : "goodbye" })
        assert_equal(graph["output"][1](), "original output")
    
    def testDoesntUpdateGeneratedFieldsIfInputsClean(self):
        updaters = [
            ("intermediate", lambda _: "constant", ("input",)),
            ("output", lambda _: "modified output", ("intermediate",))
          ]
        
        graph = filledgraphforupdaters(updaters, { "input" : "hello", "intermediate" : markgeneratedfield("constant"), "output" : markgeneratedfield("original output") }, { "input" : "goodbye" })
        assert_equal(graph["output"][1](), "original output")

    def testUpdatesBlankFieldsDependentOnNonDirtyInputs(self):
        updaters = [
            ("intermediate", lambda _: "constant", ("input",)),
            ("output", lambda _: "modified output", ("intermediate",))
          ]
        
        graph = filledgraphforupdaters(updaters, { "input" : "hello", "intermediate" : markgeneratedfield("constant"), "output" : "" }, { "input" : "goodbye" })
        assert_equal(graph["output"][1](), "modified output")
    
    def testPreferUpdatersWhichUseChangedField(self):
        short_chain_updaters = [
            ("output", lambda _: "from input one", ("input one",)),
            ("output", lambda _: "from input two", ("input two",))
          ]
        
        long_chain_updaters = [
            ("output", lambda _: "from input one", ("input one",)),
            ("intermediate", lambda x: x, ("input two",)),
            ("output", lambda _: "from input two", ("intermediate",))
          ]
        
        for updaters in [short_chain_updaters, long_chain_updaters]:
            for field, other_field in [("input one", "input two"), ("input two", "input one")]:
                # Easy: other input is missing anyway
                graph = filledgraphforupdaters(updaters, { field : "", other_field : "", "output" : "" }, { field : "go" })
                yield assert_equal, graph["output"][1](), "from " + field
            
                # Hard: other input is present
                graph = filledgraphforupdaters(updaters, { field : "", other_field : "present!", "output" : "" }, { field : "go" })
                yield assert_equal, graph["output"][1](), "from " + field

class TestUpdaterGraphUpdaters(object):
    def testEverythingEnglish(self):
        config = dict(prefersimptrad = "simp", forceexpressiontobesimptrad = False, tonedisplay = "tonified", hanzimasking = False,
                        emphasisemainmeaning = False, meaningnumbering = "circledChinese", colormeaningnumbers = False, meaningseperator = "lines",
                        audioextensions = [".mp3"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"])
        self.assertProduces({ "expression" : u"书", "mwfieldinfact" : True }, config, {
            "reading" : u'<span style="color:#ff0000">shū</span>',
            "meaning" : u'㊀ book<br />㊁ letter<br />㊂ see also <span style="color:#ff0000">\u4e66</span><span style="color:#ff0000">\u7ecf</span> Book of History',
            "mw" : u'<span style="color:#00aa00">本</span> - <span style="color:#00aa00">běn</span>, <span style="color:#0000ff">册</span> - <span style="color:#0000ff">cè</span>, <span style="color:#0000ff">部</span> - <span style="color:#0000ff">bù</span>',
            "audio" : u"[sound:" + os.path.join("Test", "shu1.mp3") + "]",
            "color" : u'<span style="color:#ff0000">书</span>',
            "trad" : u"書", "simp" : u"书"
          })

    def testEverythingGerman(self):
        config = dict(forceexpressiontobesimptrad = False, tonedisplay = "tonified",
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
        config = dict(forceexpressiontobesimptrad = False, tonedisplay = "tonified", colorizedpinyingeneration = False)
        self.assertProduces({ "expression" : u"\t书" }, config, {
            "reading" : u'\tshū',
            "color" : u'\t<span style="color:#ff0000">书</span>',
            # TODO: make the simp and trad fields preserve whitespace more reliably by moving away
            # from Google Translate as the translator. Currently this flips between preserving and
            # not preserving seemingly nondeterministically!
            "trad" : u"書", "simp" : u"书"
          })

    def testUpdateMeaningAndMWWithoutMWField(self):
        config = dict(forceexpressiontobesimptrad = False, colorizedpinyingeneration = False, emphasisemainmeaning = False,
                       meaningnumbering = "circledChinese", colormeaningnumbers = False, detectmeasurewords = True)
        self.assertProduces({ "expression" : u"啤酒", "mwfieldinfact" : False }, config, {
            "expression" : u"啤酒",
            "meaning" : u"㊀ beer<br />㊁ MW: 杯 - b\u0113i, 瓶 - p\xedng, 罐 - gu\xe0n, 桶 - t\u01d2ng, 缸 - g\u0101ng"
          })

    def testMeaningHanziMasking(self):
        config = dict(colorizedpinyingeneration = True, detectmeasurewords = False, emphasisemainmeaning = False,
                       tonedisplay = "tonified", meaningnumbering = "circledArabic", colormeaningnumbers = True, meaningnumberingcolor="#123456", meaningseperator = "custom", custommeaningseperator = " | ", prefersimptrad = "simp",
                       tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], hanzimasking = True, hanzimaskingcharacter = "MASKED")
        self.assertProduces({ "expression" : u"书", "mwfieldinfact" : False }, config, {
            "meaning" : u'<span style="color:#123456">①</span> book | <span style="color:#123456">②</span> letter | <span style="color:#123456">③</span> see also <span style="color:#123456">MASKED</span><span style="color:#ff0000">\u7ecf</span> Book of History | <span style="color:#123456">④</span> MW: <span style="color:#00aa00">本</span> - <span style="color:#00aa00">běn</span>, <span style="color:#0000ff">册</span> - <span style="color:#0000ff">cè</span>, <span style="color:#0000ff">部</span> - <span style="color:#0000ff">bù</span>',
          })

    def testMeaningSurnameMasking(self):
        config = dict(meaningnumbering = "arabicParens", colormeaningnumbers = False, meaningseperator = "lines", emphasisemainmeaning = False)
        self.assertProduces({ "expression" : u"汪", "mwfieldinfact" : False }, config, {
            "meaning" : u'(1) expanse of water<br />(2) ooze<br />(3) (a surname)',
          })

    def testMeaningChineseNumbers(self):
        self.assertProduces({ "expression" : u"九千零二十五", "mwfieldinfact" : False }, {}, { "meaning" : u'9025' })

    def testMeaningWesternNumbersYear(self):
        self.assertProduces({ "expression" : u"2001年", "mwfieldinfact" : False }, {}, { "meaning" : u'2001AD' })

    def testUpdateReadingOnly(self):
        config = dict(colorizedpinyingeneration = False, tonedisplay = "numeric")
        self.assertProduces({ "expression" : u"啤酒" }, config, { "reading" : u'pi2 jiu3' })

    def testUpdateReadingAndMeaning(self):
        config = dict(colorizedpinyingeneration = True, tonedisplay = "numeric", emphasisemainmeaning = False,
                       meaningnumbering = "arabicParens", colormeaningnumbers = True, meaningnumberingcolor = "#123456", meaningseperator = "commas", prefersimptrad = "trad",
                       tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"])
        self.assertProduces({ "expression" : u"㝵", "mwfieldinfact" : False }, config, {
             "reading" : u'<span style="color:#ffaa00">de2</span>',
             "meaning" : u'<span style="color:#123456">(1)</span> to obtain, <span style="color:#123456">(2)</span> archaic variant of <span style="color:#ffaa00">得</span> - <span style="color:#ffaa00">de2</span>, <span style="color:#123456">(3)</span> component in <span style="color:#0000ff">礙</span> - <span style="color:#0000ff">ai4</span> and <span style="color:#ffaa00">鍀</span> - <span style="color:#ffaa00">de2</span>'
          })

    def testUpdateReadingAndMeasureWord(self):
        config = dict(colorizedpinyingeneration = False, detectmeasurewords = True, tonedisplay = "numeric", prefersimptrad = "trad")
        self.assertProduces({ "expression" : u"丈夫", "mwfieldinfact" : True }, config, {
            "reading" : u'zhang4 fu',
            "mw" : u"個 - ge4"
          })

    def testUpdateReadingAndAudio(self):
        config = dict(colorizedpinyingeneration = False, tonedisplay = "tonified", audioextensions = [".mp3", ".ogg"])
        self.assertProduces({ "expression" : u"三七開", "mwfieldinfact" : False }, config, {
            "reading" : u'sān qī kāi',
            "audio" : u"[sound:" + os.path.join("Test", "san1.mp3") + "]" +
                      u"[sound:" + os.path.join("Test", "qi1.ogg") + "]" +
                      u"[sound:" + os.path.join("Test", "location/Kai1.mp3") + "]"
          })

    def testUpdateReadingAndColoredHanzi(self):
        config = dict(dictlanguage = "nonexistant", colorizedpinyingeneration = False, detectmeasurewords = False,
                       tonedisplay = "numeric", tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"])
        self.assertProduces({ "expression" : u"三峽水库" }, config, {
            "reading" : u'san1 xia2 shui3 ku4',
            "color" : u'<span style="color:#111111">三</span><span style="color:#222222">峽</span><span style="color:#333333">水</span><span style="color:#444444">库</span>'
          })

    def testUpdateReadingAndLinks(self):
        config = dict(colorizedpinyingeneration = False, detectmeasurewords = False,
                      tonedisplay = "numeric", tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"],
                      weblinks = [("YEAH!", "mytitle", "silly{searchTerms}url"), ("NAY!", "myothertitle", "verysilly{searchTerms}url")])
        self.assertProduces({ "expression" : u"一概" }, config, {
            "reading" : u'yi1 gai4',
            "weblinks" : u'[<a href="silly%E4%B8%80%E6%A6%82url" title="mytitle">YEAH!</a>] [<a href="verysilly%E4%B8%80%E6%A6%82url" title="myothertitle">NAY!</a>]'
          })

    def testReadingFromWesternNumbers(self):
        config = dict(colorizedpinyingeneration = True, tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"])
        self.assertProduces({ "expression" : u"111" }, config, {
            "reading" : u'<span style="color:#333333">b\u01cei</span> <span style="color:#111111">y\u012b</span> <span style="color:#222222">sh\xed</span> <span style="color:#111111">y\u012b</span>'
          })

    def testNotifiedUponAudioGenerationWithNoPacks(self):
        config = dict(colorizedpinyingeneration = False, detectmeasurewords = False, tonedisplay = "numeric")
        
        def nassert(notifier):
            assert_equal(len(notifier.infos), 1)
            assert_true("cannot" in notifier.infos[0])
        
        self.assertProduces({ "expression" : u"三月", "mwfieldinfact" : False }, config, {
            "reading" : u'san1 yue4', "audio" : None
          }, mediapacks=[], notifierassertion=nassert)

    def testUpdateMeasureWordAudio(self):
        config = dict(audioextensions = [".mp3", ".ogg"])
        
        pack = media.MediaPack("MWAudio", updated(identitymediadict(["pi2", "bei1", "ping2", "guan4", "tong3", "tong2", "gang1"]), quantitydigitmediadict))

        def mwaudioassert(mwaudio):
            # jiu3 in the numbers aliases with jiu3 in the characters :(
            sounds = ["X", "bei1", "pi2", "X",
                      "X", "ping2", "pi2", "X",
                      "X", "guan4", "pi2", "X",
                      "X", "tong3", "pi2", "X",
                      "X", "gang1", "pi2", "X"]
            assert_equal(sanitizequantitydigits(mwaudio), "".join([u"[sound:" + os.path.join("MWAudio", sound + ".mp3") + "]" for sound in sounds]))

        # NB: turning off meaninggeneration here triggers a bug that happened in 0.6 where
        # we wouldn't set up the dictmeasurewords for the mwaudio
        self.assertProduces({ "expression" : u"啤酒" }, config, { "mwaudio" : mwaudioassert }, mediapacks=[pack])

    def testFallBackOnGoogleForPhrase(self):
        config = dict(fallbackongoogletranslate = True, colorizedpinyingeneration = False, detectmeasurewords = False,
                       tonedisplay = "numeric", hanzimasking = False)
        self.assertProduces({ "expression" : u"你好，你是我的朋友吗", "mwfieldinfact" : False }, config, {
            "reading" : u'ni3 hao3, ni3 shi4 wo3 de peng2 you ma',
            "meaning" : u'Hello, you are my friend do<br /><span style="color:gray"><small>[Google Translate]</small></span><span> </span>'
          })

    def testUpdateSimplifiedTraditional(self):
        config = dict(simpgeneration = True, tradgeneration = True)
        self.assertProduces({ "expression" : u"个個" }, config, {
            "simp"  : u"个个",
            "trad" : u"個個"
          })

    def testUpdateReadingAndColoredHanziAndAudioWithSandhi(self):
        config = dict(colorizedpinyingeneration = True, detectmeasurewords = False, audioextensions = [".mp3"], tonedisplay = "numeric",
                      tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"])
        self.assertProduces({ "expression" : u"很好", "mwfieldinfact" : False }, config, {
            "reading" : u'<span style="color:#66cc66">hen3</span> <span style="color:#00aa00">hao3</span>',
            "color" : u'<span style="color:#66cc66">很</span><span style="color:#00aa00">好</span>',
            "audio" : u"[sound:" + os.path.join("Test", "hen2.mp3") + "]" +
                      u"[sound:" + os.path.join("Test", "hao3.mp3") + "]"
          })

    def testUpdateSimplifiedTraditionalDoesNothingIfSimpTradIdentical(self):
        self.assertProduces({ "expression" : u"鼠" }, {}, { "simp"  : u"", "trad" : u"" })

    def testUpdateColoredCharactersFromReading(self):
        config = dict(colorizedcharactergeneration = True, tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"])
        
        for reading in [u"chi1 fan1", u"chī fān", u'<span style="color:#ff0000">chī</span> <span style="color:#ff0000">fān</span>']:
            yield (lambda reading: self.assertProduces({ "reading" : reading, "expression" : u"吃饭" }, config, {
                "reading" : reading,
                "color" : u'<span style="color:#ff0000">吃</span><span style="color:#ff0000">饭</span>'
              }), reading)

    def assertProduces(self, known, configdict, expected, mediapacks=None, notifierassertion=None):
        if mediapacks == None:
            mediapacks = [media.MediaPack("Test", { "shu1.mp3" : "shu1.mp3", "shu1.ogg" : "shu1.ogg",
                                                    "san1.mp3" : "san1.mp3", "qi1.ogg" : "qi1.ogg", "Kai1.mp3" : "location/Kai1.mp3",
                                                    "hen3.mp3" : "hen3.mp3", "hen2.mp3" : "hen2.mp3", "hao3.mp3" : "hao3.mp3" })]
        
        if notifierassertion == None:
            notifierassertion = lambda notifier: assert_equal(len(notifier.infos), 0)
        
        notifier = MockNotifier()
        gbu = GraphBasedUpdater(notifier, MockMediaManager(mediapacks), pinyin.config.Config(pinyin.utils.updated({ "dictlanguage" : "en" }, configdict)))
        graph = gbu.filledgraph({}, known)
        
        assert_dict_equal(dict([(key, graph[key][1]()) for key in expected.keys()]), expected, values_as_assertions=True)
        notifierassertion(notifier)