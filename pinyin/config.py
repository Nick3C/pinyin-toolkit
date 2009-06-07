#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

import dictionary
import dictionaryonline
from logger import log

# TODO: expose these things in the UI
#  * Audio file extension list
#  * User colors
#  * Candidate field names
#  * Deck tag
#  * Color option for the line-index (cute symbols)
# * link generator (and a list of the links to be generated)

defaultsettings = {
    "dictlanguage" : "en",

    "colorizedpinyingeneration"    : True, # Should we try and write readings and measure words that include colorized pinyin?
    "colorizedcharactergeneration" : True, # Should we try and fill out a field called Color with a colored version of the character?
    
    "audiogeneration"              : True, # Should we try and fill out a field called Audio with text-to-speech commands?
    
    "meaninggeneration"            : True, # Should we try and fill out a field called Meaning with the definition? 
    "fallbackongoogletranslate"    : True, # Should we use Google to fill out the Meaning field if needs be? 
    "detectmeasurewords"           : True, # Should we try and put measure words seperately into a field called MW?
    "hanzimasking"                 : True, # Should Hanzi masking be turned on? i.e. if the expression appears in the meaning field be replaced with a "㊥" or "[~]"
    "colormeaningnumbers"          : True, # Should we color the index number for each translation a different color?
    
    "weblinkgeneration"            : True, # Should we try to generate some online dictionary references for each card into a field called Links?
    
    # Unimplemented flags (why did Nick add these???)
    "generatepos"                  : True, # Should we try to generate the POS (part of Speech) from dictionaries?
    "enablefeedback"               : True, # Should support for submitting entries to CEDICT, etc be turned on?
    "tonesandhiconvert"            : True, # Should the tone sandhi tones: (3, 3) be colored differently
    
    # "numeric" or "tonified"
    "tonedisplay" : "tonified",

    # "circledChinese", "circledArabic", "arabicParens" or "none"
    "meaningnumbering" : "circledChinese",

    # "lines", "commas" or "custom"
    "meaningseperator" : "lines",
    "custommeaningseperator" : " | ",

    # "simp" or "trad"
    "prefersimptrad" : "simp",

    # Descending order of priority (default is prefer ".ogg" and dislike ".wav"]
    "audioextensions" : [".ogg", ".mp3", ".wav"],

    # You should not have to change this setting as it defaults to a free and usable sound-set.
    # Be aware that you may be able to find higher quality audio files from other sources.
    "mandarinsoundsurl" : "http://www.chinese-lessons.com/sounds/Mandarin_sounds.zip",
    
    # The character to use for hanzi masking in meanings: ~ or [~] are obvious alternatives
    "hanzimaskingcharacter" : u"㊥",

    "tonecolors" : [
        u"#ff0000", # red
        u"#ffaa00", # orange
        u"#00aa00", # green
        u"#0000ff", # blue
        u"#545454", # grey
        # This should not be in in this array. This is for actual tones only:
        # u"#66CC66", # tone sandhi
      ],
    
    "meaningnumberingcolor" : "#A4A4A4", # grey

    "extraquickaccesscolors" : [
        u"#000000",  # black         (not the same as 'no color')
        u"#00AAFF",  # light blue    (suggested alternative text color)
        u"#55007F",  # yellow        (suggested highlighting color)
        u"#32CD32",  # dark green    (candidate for future tone sandhi color) 
        u"#C71585",  # violet        (randomly chosen default color)
        u"#FF6347",  # tomato        (random chosen default color)
        u"#7FFF00"   # light green   (random chosen default color)
      ],

    # Field names are listed in descending order of priority
    "candidateFieldNamesByKey" : {
        'expression' : ["Expression", "Hanzi", "Chinese", u"汉字", u"中文"],
        'reading'    : ["Reading", "Pinyin", "PY", u"拼音"],
        'meaning'    : ["Meaning", "Definition", "English", "German", "French", u"意思", u"翻译", u"英语", u"法语", u"德语"],
        'audio'      : ["Audio", "Sound", "Spoken", u"声音"],
        'color'      : ["Color", "Colour", "Colored Hanzi", u"彩色"],
        'mw'         : ["MW", "Measure Word", "Classifier", u"量词"],
        'weblinks'   : ["Links", "Link", "LinksBar", "Links Bar", "Link Bar", "LinkBar", "Web", "Dictionary", "URL", "URLs"],
        'pos'        : ["POS", "Part", "Type", "Cat", "Class", "Kind", "Grammar"] 
      },
    
    # Links occur in the order that they will be shown in the file
    "weblinks" : [
      ('e',       'Submit CC-CEDICT entry', 'http://cc-cedict.org/editor/editor.php?handler=InsertSimpleEntry&popup=0&insertsimpleentry_hanzi_simplified={searchTerms}'),
      ('nckiu',   'nckiu',                  'http://www.nciku.com/mini/all/{searchTerms}'),
      ('CEDICT',  'CC-CEDICT at MDBG',      'http://www.mdbg.net/chindict/chindict.php?page=worddictbasic&wdqb={searchTerms}'),
      ('WikiD',   'Wiki Dictionary',        'http://en.wiktionary.org/wiki/{searchTerms}'),
      ('YellowB', 'Yellow Bridge',          'http://www.yellowbridge.com/chinese/charsearch.php?searchChinese=1&zi={searchTerms}')
    ],
    
    # Only decks with this tag are processed
    "modelTag" : "Mandarin"
  }

tonedisplayshouldtonify = {
    "numeric" : False,
    "tonified" : True
}

meaningnumberingstringss = {
    # Cute Chinese symbols for first 10, then english up to 20
    "circledChinese" : [u"㊀", u"㊁", u"㊂", u"㊃", u"㊄", u"㊅", u"㊆", u"㊇", u"㊈", u"㊉", u"⑪", u"⑫", u"⑬", u"⑭", u"⑮", u"⑯", u"⑰", u"⑱", u"⑲", u"⑳"],
    # Cute Chinese symbols for first 10, then double symbols up to 20
    #"circledChinese" : [u"㊀", u"㊁", u"㊂", u"㊃", u"㊄", u"㊅", u"㊆", u"㊇", u"㊈", u"㊉㊀", u"㊉㊁", u"㊉㊂", u"㊉㊃", u"㊉㊄", u"㊉㊅", u"㊉㊆", u"㊉㊇", u"㊉㊈", u"㊁㊉"],
    "circledArabic" : [u"①", u"②", u"③", u"④", u"⑤", u"⑥", u"⑦", u"⑧", u"⑨", u"⑩", u"⑪", u"⑫", u"⑬", u"⑭", u"⑮", u"⑯", u"⑰", u"⑱", u"⑲", u"⑳"],
    "arabicParens" : [],
    "none" : None
  }

meaningseperatorstrings = {
    "lines": "<br />",
    "commas" : ", "
  }

"""
Pinyin Toolkit configuration object: this will be pickled
up and stored into Anki's configuration database.  To allow
extension of this class in the future, I only pickle up the
key/value pairs stored in the user data field.
"""
class Config(object):
    # NB: DO NOT store anything of importance into this class other than the settings dictionary.
    # Any such data won't be saved between sessions!
    
    # In general, this object should be created using unpickling rather than just constructed
    def __init__(self, usersettings=None):
        settings = {}
        
        # Set all settings first using the defaults and then by coping the user settings
        for key, value in defaultsettings.items() + (usersettings or {}).items():
            # Because of a BUG a previous versions, users might have some private
            # data in their settings.  Filter that out here.
            # NB: this special case is just to make Nick's life easier.  Should be able
            # to remove it once he has run the new version at least once.
            if "_Config__" in key:
                continue
            
            settings[key] = copy.deepcopy(value)
        
        log.info("Initialized configuration with settings %s", settings)
        self.settings = settings
        
        # /Transient/ flag recording whether Google translate appears to be up. To begin
        # with, we aren't sure
        self.__googletranslateworking = None
    
    #
    # The pickle protocol (http://docs.python.org/library/pickle.html#pickle.Pickler)
    #
    
    def __getstate__(self):
        return self.settings
    
    def __setstate__(self, settings):
        self.settings = settings
    
    #
    # Attribute protocol
    #
    
    def __getattr__(self, name):
        # NB: we want to ensure that:
        # 1) Allow reading of the settings dictionary itself
        # 2) Look up the name on the class for consistency
        # 3) Reading of transient data like __googletranslateworking goes to the instance
        if "settings" in self.__dict__ and name in self.__dict__["settings"]:
            return self.__dict__["settings"][name]
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        # 1) Allow writing of the settings dictionary itself
        # 2) Look up the name on the class to ensure that we can write to properties!!
        #    See <http://mail.python.org/pipermail/python-list/2002-January/124867.html>
        # 3) Writes to transient properties go to the instance
        if "settings" in self.__dict__ and name in self.__dict__["settings"]:
            self.__dict__["settings"][name] = value
        else:
            object.__setattr__(self, name, value)
    
    #
    # Derived settings
    #
    
    # The reason that it's not totally insane to load the dictionary upon every property access is that secretly
    # the dictionary keeps a cache of the most recently loaded ones from which it can satisfy this request
    dictionary = property(lambda self: dictionary.PinyinDictionary.load(self.dictlanguage, self.needmeanings))
    
    shouldtonify = property(lambda self: tonedisplayshouldtonify[self.tonedisplay])
    needmeanings = property(lambda self: self.meaninggeneration or self.detectmeasurewords)
    meaningnumberingstrings = property(lambda self: meaningnumberingstringss[self.meaningnumbering])
    meaningseperatorstring = property(lambda self: meaningseperatorstrings.get(self.meaningseperator) or self.custommeaningseperator)
    
    def formatmeanings(self, meanings):
        # Don't add meaning numbers if it is disabled or there is only one meaning
        if len(meanings) > 1 and self.meaningnumberingstrings != None:
            def meaningnumber(n):
                if n < len(self.meaningnumberingstrings):
                    number = self.meaningnumberingstrings[n]
                else:
                    # Ensure that we fall back on normal (n) numbers if there are more numbers than we have in the supplied list
                    number = '(' + str(n + 1) + ')'

                if self.colormeaningnumbers:
                    return '<span style="color:' + self.meaningnumberingcolor + '">' + number + '</span>'
                else:
                    return number
        
            # Add numbers to all the meanings in the list
            meanings = [meaningnumber(n) + " " + meaning for n, meaning in enumerate(meanings)]
        
        # Use the seperator to join the meanings together
        return self.meaningseperatorstring.join(meanings)
    
    def getshouldusegoogletranslate(self):
        # Fail fast if the user has turned Google off:
        if not self.fallbackongoogletranslate:
            return False

        # Determine the status of Google Translate if we haven't already done so.
        # TODO: should try every 5 minutes or something rather than giving up on first failure.
        if self.__googletranslateworking == None:
            # Test internet connectivity by performing a gTrans call.
            # If this call fails then translations are disabled until Anki is restarted.
            # This prevents a several second delay from occuring when changing a field with no internet
            self.__googletranslateworking = dictionaryonline.gCheck(self.dictlanguage)
            log.info("Google Translate has tested internet access and reports status %s", self.__googletranslateworking)

        # Only use it if it appears to be working
        return self.__googletranslateworking

    shouldusegoogletranslate = property(getshouldusegoogletranslate)
    
    #
    # Color accessors
    #
    
    def arrayproperty(attr, n):
        def setter(self, value):
            getattr(self, attr)[n] = value
        
        return property(lambda self: getattr(self, attr)[n], setter)
    
    tone1color = arrayproperty("tonecolors", 0)
    tone2color = arrayproperty("tonecolors", 1)
    tone3color = arrayproperty("tonecolors", 2)
    tone4color = arrayproperty("tonecolors", 3)
    tone5color = arrayproperty("tonecolors", 4)
    
    extraquickaccess1color = arrayproperty("extraquickaccesscolors", 0)
    extraquickaccess2color = arrayproperty("extraquickaccesscolors", 1)
    extraquickaccess3color = arrayproperty("extraquickaccesscolors", 2)
    extraquickaccess4color = arrayproperty("extraquickaccesscolors", 3)
    extraquickaccess5color = arrayproperty("extraquickaccesscolors", 4)
    extraquickaccess6color = arrayproperty("extraquickaccesscolors", 5)
    extraquickaccess7color = arrayproperty("extraquickaccesscolors", 6)


if __name__=='__main__':
    import unittest
    
    class ConfigTest(unittest.TestCase):
        def testPickle(self):
            import pickle
            config = Config({ "setting" : "value", "cheese" : "mice" })
            self.assertEquals(pickle.loads(pickle.dumps(config)).settings, config.settings)
    
        def testAttribute(self):
            self.assertEquals(Config({ "key" : "value" }).key, "value")
        
        def testIndexedAttribute(self):
            self.assertEquals(Config({ "key" : ["value"] }).key[0], "value")
    
        def testMissingAttribute(self):
            self.assertRaises(AttributeError, lambda: Config({ "key" : ["value"] }).kay)
        
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
        
        def testToneAccessors(self):
            config = Config({ "tonecolors" : ["1", "2"]})
            self.assertEquals(config.tone1color, "1")
            
            config.tone1color = "hi"
            self.assertEquals(config.tone1color, "hi")
        
        def testExtraQuickAccessAcessors(self):
            config = Config({ "extraquickaccesscolors" : ["1", "2"] })
            self.assertEquals(config.extraquickaccess2color, "2")
            
            config.extraquickaccess2color = "bye"
            self.assertEquals(config.extraquickaccess2color, "bye")
        
        def testDictionary(self):
            self.assertEquals(Config({ "dictlanguage" : "en", "meaninggeneration" : True }).dictionary, dictionary.PinyinDictionary.load("en", True))
        
        def testTonified(self):
            self.assertTrue(Config({ "tonedisplay" : "tonified" }).shouldtonify)
            self.assertFalse(Config({ "tonedisplay" : "numeric" }).shouldtonify)
        
        def testNeedMeanings(self):
            self.assertTrue(Config({ "meaninggeneration" : True, "detectmeasurewords" : True }).needmeanings)
            self.assertTrue(Config({ "meaninggeneration" : True, "detectmeasurewords" : False }).needmeanings)
            self.assertTrue(Config({ "meaninggeneration" : False, "detectmeasurewords" : True }).needmeanings)
            self.assertFalse(Config({ "meaninggeneration" : False, "detectmeasurewords" : False }).needmeanings)
        
        def testFormatMeaningsOptions(self):
            self.assertEquals(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "lines", "colormeaningnumbers" : False }).formatmeanings([u"a", u"b"]),
                              u"(1) a<br />(2) b")
            self.assertEquals(Config({ "meaningnumbering" : "circledChinese", "meaningseperator" : "commas", "colormeaningnumbers" : False }).formatmeanings([u"a", u"b"]),
                              u"㊀ a, ㊁ b")
            self.assertEquals(Config({ "meaningnumbering" : "circledArabic", "meaningseperator" : "custom", "custommeaningseperator" : " | ", "colormeaningnumbers" : False }).formatmeanings([u"a", u"b"]),
                              u"① a | ② b")
            self.assertEquals(Config({ "meaningnumbering" : "none", "meaningseperator" : "custom", "custommeaningseperator" : " ^_^ ", "colormeaningnumbers" : False }).formatmeanings([u"a", u"b"]),
                              u"a ^_^ b")
            self.assertEquals(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "lines", "colormeaningnumbers" : True, "meaningnumberingcolor" : "#aabbcc" }).formatmeanings([u"a", u"b"]),
                            u'<span style="color:#aabbcc">(1)</span> a<br /><span style="color:#aabbcc">(2)</span> b')
        
        def testFormatMeaningsSingleMeaning(self):
            self.assertEquals(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "lines" }).formatmeanings([u"a"]), u"a")
        
        def testFormatTooManyMeanings(self):
            self.assertEquals(Config({ "meaningnumbering" : "circledChinese", "meaningseperator" : "commas", "colormeaningnumbers" : False }).formatmeanings([str(n) for n in range(1, 22)]),
                              u"㊀ 1, ㊁ 2, ㊂ 3, ㊃ 4, ㊄ 5, ㊅ 6, ㊆ 7, ㊇ 8, ㊈ 9, ㊉ 10, ⑪ 11, ⑫ 12, ⑬ 13, ⑭ 14, ⑮ 15, ⑯ 16, ⑰ 17, ⑱ 18, ⑲ 19, ⑳ 20, (21) 21")
    
        def testShouldUseGoogleTranslateDontUse(self):
            self.assertFalse(Config({ "fallbackongoogletranslate" : False }).shouldusegoogletranslate)
            
        def testShouldUseGoogleTranslateShouldUse(self):
            self.assertTrue(Config({ "fallbackongoogletranslate" : True }).shouldusegoogletranslate)
    
    unittest.main()