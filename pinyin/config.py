#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

import dictionaryonline
import utils
from logger import log

# TODO: expose these things in the UI
#  * Audio file extension list
#  * User colors
#  * Candidate field names
#  * Deck tag
#  * Color option for the line-index (cute symbols)
# * link generator (and a list of the links to be generated)

defaultsettings = {
    # The idea here is that we can mark the version of the configuration
    # information that the config was last processed by, so that we can
    # upgrade it over time. TODO: implement the actual upgrade logic.
    "version" : 1,

    "dictlanguage" : "en",

    "colorizedpinyingeneration"    : True, # Should we try and write readings and measure words that include colorized pinyin?
    "colorizedcharactergeneration" : True, # Should we try and fill out a field called Color with a colored version of the character?
    
    "audiogeneration"              : True, # Should we try and fill out a field called Audio with text-to-speech commands?
    "mwaudiogeneration"            : True, # Should we try and fill out a field called MW Audio with measure word text-to-speech commands?
    "readinggeneration"            : True, # Should we try and fill out a field called Reading with pinyin?
    
    "meaninggeneration"            : True, # Should we try and fill out a field called Meaning with the definition? 
    "fallbackongoogletranslate"    : True, # Should we use Google to fill out the Meaning field if needs be? 
    "detectmeasurewords"           : True, # Should we try and put measure words seperately into a field called MW?
    "hanzimasking"                 : True, # Should Hanzi masking be turned on? i.e. if the expression appears in the meaning field be replaced with a "㊥" or "[~]"
    "colormeaningnumbers"          : True, # Should we color the index number for each translation a different color?
    "emphasisemainmeaning"         : True, # Should we format the meanings so that the most frequent one is called out?
    
    "weblinkgeneration"            : False, # Should we try to generate some online dictionary references for each card into a field called Links?
    
    "tradgeneration"               : False, # Should we try to generate traditional Chinese readings from the main entry?
    "simpgeneration"               : False, # Should we try to generate simplified Chinese reading from the main entry
    "forceexpressiontobesimptrad"  : False, # Should we try to replace the contents of the Expression field with the preferred character set?
                                            # This ensure, for example, they your simplified deck only has simplified in the Expression field
                                            # note: the setting "prefersimptrad" controls what is populated into the Expression field
    
    "forcereadingtobeformatted"        : True,  # Should we try and update the reading with a colored, appropriately tonified variant?
    "forcemeaningnumberstobeformatted" : True,  # Should we try and format numbers in the meaning as their fancy variant?
    "forcepinyininaudiotosoundtags"    : True,  # Should we try and replace pinyin in the audio field with the corresponding audio?
    
    # Unimplemented flags (for dev purposes)
    #"posgeneration"                : True, # Should we try to generate the POS (part of Speech) from dictionaries?
    #"enablefeedback"               : True, # Should support for submitting entries to CEDICT, etc be turned on?
    
    # "numeric" or "tonified"
    "tonedisplay" : "tonified",

    # "circledChinese", "circledArabic", "arabicParens" or "none"
    "meaningnumbering" : "circledChinese",

    # "lines", "commas" or "custom"
    "meaningseperator" : "lines",
    "custommeaningseperator" : " | ",

    # Tag to use to wrap around non-emphasised meanings: if it ends with a /, then
    # the tag is treated as self-closing and only the leading tag will be added
    "mainmeaningemphasistag" : "small",

    # "simp" or "trad" - used for both determining which kind of measure word to
    # show and which kind of character to use to fill the expression field
    "prefersimptrad" : "simp",

    # Descending order of priority (default is prefer ".ogg" and dislike ".wav"]
    # Default list taken from http://en.wikipedia.org/wiki/Audio_file_format (as Anki plays anything mplayer can play)
    "audioextensions" : [".ogg", ".mp3", ".wav", ".mp4", ".m4a", ".wma", ".aac", ".voc", ",mpc", ".mpc", ".flac", ".aiff", ".raw", ".au", ".vox", ".dct", ".gsm", ".mmf", ".ra", ".ram", ".m4p", ".msv"],

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
        # u"#32CD32",  # dark green    (candidate for future tone sandhi color) 
        # u"#C71585",  # violet        (randomly chosen default color)
        # u"#FF6347",  # tomato        (random chosen default color)
        # u"#7FFF00"   # light green   (random chosen default color)
      ],
    
    # Links occur in the order that they will be shown in the file
    #
    # Change MDBG submit to match:
    # http://cc-cedict.org/editor/editor.php?handler=InsertSimpleEntry&popup=1&insertsimpleentry_old_cedict=語言障礙+语言障碍+[yu3+yan2+zhang4+ai4]+/speech+defect/
    # 
    # 
    # need to deal with unicode encoding first
    # great, add it       http://hmarty.free.fr/hanzi/
    # alright but ugly    http://humanum.arts.cuhk.edu.hk/cgi-bin/agrep-lindict?query=test&category=full&boo=no&ignore=on&substr=on&order=all
    # not so good         http://cdict.net/?q=%AD%FC
    # 
    # need to crack javascript:
    # AMAZING         http://www.zdic.net/    [largest encyclopedia in china)
    "weblinks" : [
      ('e',       'Submit CC-CEDICT entry',  'http://cc-cedict.org/editor/editor.php?handler=InsertSimpleEntry&popup=0&insertsimpleentry_hanzi_simplified={searchTerms}'),
      ('nCiku',   'nCiku',                   'http://www.nciku.com/mini/all/{searchTerms}'),
      ('CEDICT',  'CC-CEDICT at MDBG',       'http://www.mdbg.net/chindict/chindict.php?page=worddictbasic&wdqb={searchTerms}'),
      ('Dict.cn', 'Dict.cn',                 'http://dict.cn/{searchTerms}'),
      ('Iciba',   'Iciba',                   'http://love.iciba.com//?{searchTerms}/?'),
      (u'互动百科',   'Hudong',                  'http://www.hudong.com/wiki/{searchTerms}'),
      ('Unihan',  'Unicode Unihan Database', 'http://www.unicode.org/cgi-bin/GetUnihanData.pl?codepoint={searchTerms}'),
      #('WikiD',   'Wiktionary',              'http://en.wiktionary.org/wiki/{searchTerms}'), # Not that good yet
      ('YellowB', 'Yellow Bridge',           'http://www.yellowbridge.com/chinese/charsearch.php?searchChinese=1&zi={searchTerms}'),
      (u'有道',     'Youdao',                  'http://dict.youdao.com/search?q={searchTerms}&btnindex=&ue=utf8&keyfrom=dict.index'),
      (u'雅虎',     'Zidian',                  'http://zidian.cn.yahoo.com/result_cn2en.html?p={searchTerms}')
    ],
    
    # Only decks with this tag are processed
    "modelTag" : "Mandarin",

    # Field names are listed in descending order of priority
    "candidateFieldNamesByKey" : utils.let(
            ["MW", "Measure Word", "Classifier", "Classifiers", u"量词"],
            ["Audio", "Sound", "Spoken", u"声音"],
            lambda mwfields, audiofields: {
        'expression' : ["Expression", "Hanzi", "Chinese", "Character", "Characters", u"汉字", u"中文"],
        'reading'    : ["Reading", "Pinyin", "PY", u"拼音"],
        'meaning'    : ["Meaning", "Definition", "English", "German", "French", u"意思", u"翻译", u"英语", u"法语", u"德语"],
        'audio'      : audiofields,
        'color'      : ["Color", "Colour", "Colored Hanzi", u"彩色"],
        'mw'         : mwfields,
        'mwaudio'    : utils.concat(utils.concat([[[x + " " + y, x + y] for x in mwfields] for y in audiofields])),
        #'weblinks'   : ["Links", "Link", "LinksBar", "Links Bar", "Link Bar", "LinkBar", "Web", "Dictionary", "URL", "URLs"],
        #'pos'        : ["POS", "Part", "Type", "Cat", "Class", "Kind", "Grammar"] ,
        'trad'       : ["Traditional", "Trad", "Traditional Chinese", "HK", u'繁体字', u'繁体', u"繁體字", u"繁體"],
        'simp'       : ["Simplified", "Simp", "Simplified Chinese", u"简体字", u"简体"]
      })
  }

updatecontrolflags = {
    'expression' : None,
    'reading'    : "readinggeneration",
    'meaning'    : "meaninggeneration",
    'mw'         : "detectmeasurewords",
    'audio'      : "audiogeneration",
    'mwaudio'    : "mwaudiogeneration",
    'color'      : "colorizedcharactergeneration",
    'trad'       : "tradgeneration",
    'simp'       : "simpgeneration",
    'weblinks'   : "weblinkgeneration"
}

tonedisplayshouldtonify = {
    "numeric" : False,
    "tonified" : True
}

meaningnumberingstringss = utils.let(
    # I would love to include u"㉑", u"㉒", u"㉓", u"㉔", u"㉕", u"㉖", u"㉗", u"㉘", u"㉙", u"㉚"
    # as well, but they are part of "Enclosed CJK Letters and Months", and Windows font
    # vendors don't seem to supply this group. Up to ⑳ are in "Enclosed Alphanumerics"
    # and are supplied in at least Arial Unicode MS.
    #
    # Annoyingly, this means that non-broken platforms like OS X get bad numbers above 20.
    [u"⑪", u"⑫", u"⑬", u"⑭", u"⑮", u"⑯", u"⑰", u"⑱", u"⑲", u"⑳"],
    lambda elevenOnwards: {
    # Cute Chinese symbols for first 10, then english up from there
    "circledChinese" : [u"㊀", u"㊁", u"㊂", u"㊃", u"㊄", u"㊅", u"㊆", u"㊇", u"㊈", u"㊉"] + elevenOnwards,
    # Cute Chinese symbols for first 10, then double symbols up to 20
    #"circledChinese" : [u"㊀", u"㊁", u"㊂", u"㊃", u"㊄", u"㊅", u"㊆", u"㊇", u"㊈", u"㊉㊀", u"㊉㊁", u"㊉㊂", u"㊉㊃", u"㊉㊄", u"㊉㊅", u"㊉㊆", u"㊉㊇", u"㊉㊈", u"㊁㊉"],
    "circledArabic" : [u"①", u"②", u"③", u"④", u"⑤", u"⑥", u"⑦", u"⑧", u"⑨", u"⑩"] + elevenOnwards,
    "arabicParens" : [],
    "none" : None
  })

meaningseperatorstrings = {
    "lines": "<br />",
    "commas" : ", "
  }

#
# The framework of 'incorporations' that I use to upgrade the configuration data.
# Can be nested arbitrarily deeply for awesome hierarchical update power!
#

def incorporatebydeepcopy(existing, new):
    return copy.deepcopy(new)

def incorporatepositionallist(incorporations):
    def inner(existing, new):
        # Ensure that we leave the size of the existing list unchanged,
        # but incorporate any changes in the elements
        for n in range(0, min(len(existing), len(new))):
            incorporation = n < len(incorporations) and incorporations[n] or incorporatebydeepcopy
            existing[n] = incorporation(existing[n], new[n])
    
        return existing

    return inner

def incorporatebykeydict(incorporations):
    def inner(existing, new):
        for key, value in new.items():
            # This setting might have disappeared entirely or been renamed.
            # In that case, throw away the "new" data we've just sucked in
            if key not in existing:
                continue
        
            # Use the supplied incorporations to recursively merge the data
            # stored in the values of the dictionary
            existing[key] = incorporations.get(key, incorporatebydeepcopy)(existing[key], value)
        
        return existing
    
    return inner

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
        
        # Set all settings first by deep-copying the defaults. These are in an authoratitive
        # format and guaranteed to work with the current Toolkit version
        for key, value in defaultsettings.items():
            settings[key] = copy.deepcopy(value)
        
        # Now incorporate any saved settings. Here we have to be careful, because the stuff
        # we're sucking in might have screwy stuff in it from the old days. The point of the
        # incorporations framework is to try and move as much stuff from the user into the
        # settings as possible without screwing up the fine structure of the settings and making
        # the toolkit inoperable:
        settings = incorporatebykeydict({
                "tonecolors" : incorporatepositionallist({}),
                "extraquickaccesscolors" : incorporatepositionallist({}),
                "candidateFieldNamesByKey" : incorporatebykeydict({})
            })(settings, usersettings or {})
        
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
    
    shouldtonify = property(lambda self: tonedisplayshouldtonify[self.tonedisplay])
    needmeanings = property(lambda self: self.meaninggeneration or self.detectmeasurewords)
    meaningnumberingstrings = property(lambda self: meaningnumberingstringss[self.meaningnumbering])
    meaningseperatorstring = property(lambda self: meaningseperatorstrings.get(self.meaningseperator) or self.custommeaningseperator)
    
    def meaningnumber(self, n):
        if self.meaningnumberingstrings is None:
            return ""
        
        if n <= len(self.meaningnumberingstrings):
            number = self.meaningnumberingstrings[n - 1]
        else:
            # Ensure that we fall back on normal (n) numbers if there are more numbers than we have in the supplied list
            number = '(' + str(n) + ')'

        if self.colormeaningnumbers:
            return '<span style="color:' + self.meaningnumberingcolor + '">' + number + '</span>'
        else:
            return number
    
    def numbermeanings(self, meanings, offset):
        # Don't add meaning numbers if it is disabled or there is only one meaning
        if len(meanings) > 1 and self.meaningnumberingstrings != None:
            # Add numbers to all the meanings in the list
            return self.meaningseperatorstring.join([self.meaningnumber(offset + n + 1) + " " + meaning for n, meaning in enumerate(meanings)])
        else:
            # Concatenate together all the meanings directly
            return self.meaningseperatorstring.join(meanings)
    
    def formatmeanings(self, meanings):
        if self.emphasisemainmeaning and len(meanings) > 1:
            # Call out the first meaning specially
            starttag, endtag = self.mainmeaningemphasistag.endswith("/") and ("<%s />" % self.mainmeaningemphasistag[:-1], "") \
                                                                          or ("<%s>" % self.mainmeaningemphasistag, "</%s>" % self.mainmeaningemphasistag)
            return meanings[0] + self.meaningseperatorstring + starttag + self.numbermeanings(meanings[1:], 1) + endtag
        else:
            # No header, just format all the meanings together
            return self.numbermeanings(meanings, 0)
    
    def formathanzimaskingcharacter(self):
        if self.colormeaningnumbers:
            return '<span style="color:' + self.meaningnumberingcolor + '">' + self.hanzimaskingcharacter + '</span>'
        else:
            return self.hanzimaskingcharacter
    
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
