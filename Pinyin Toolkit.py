#!/usr/bin/env python
# -*- coding: utf-8 -*-
########################################################################
###                   Mandarin-Chinese Pinyin Toolkit                ### 
########################################################################
# A Plugin for the Anki Spaced Repition learning system <http://ichi2.net/anki/>

#    Mandarin-Chinese Pinyin Toolkit
#    Copyright (C) 2009 Nicholas Cook & Max Bolingbroke

#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


###############  Version Details ###############
pinyin_toolkit="0.05 dev feature complete 0.1"

CCDict_Ver="2009-05-29T05:46:28Z" # [n=84885] http://www.mdbg.net/chindict/chindict.php?page=cc-cedict
HanDeDict_Ver="Sat May 30 00:20:38 2009" # [n=169500] http://www.chinaboard.de/chinesisch_deutsch.php?mode=dl&w=8
CFDICT_Ver="Wed Jan 21 01:49:53 2009" # [n=593] http://www.chinaboard.de/fr/cfdict.php?mode=dl&w=8
# Note that these dictionaries are not identical and have important formatting differences and field order variation

############  Language Masterswitch  ############
# The following option controls the language used for translation and dictionary lookup.
# uncomment your preference or add a new entry
dictlanguage="en"    # English (en):         Full support (online and offline)
#dictlanguage="de"   # German (de):          Full support (online and offline)
#dictlanguage="fr"   # French (fr):          Hybrid support (online and partial offline)

                     # ALL OTHER LANGUAGES:  Online Support only
#dictlanguage="es"   # Spanish  (es)
#dictlanguage="hi"   # Hindi (hi)
#dictlanguage="pt"   # Portugese  (pt)
#dictlanguage="ar"   # Arabic (ar)
#dictlanguage="bn"   # Bengali (bn)
#dictlanguage="ru"   # Russian (ru)
#dictlanguage="ja"   # Japanese (ja)

# To find the language code for your language go here: http://www.loc.gov/standards/iso639-2/php/code_list
# Note that languages with Full (and partial) support can access additional features and benefits.

############### Settings Section ###############

### Options ###

tonify                       = True   # Should we output tone marks rather than numbers on pinyin? True or False
colorizedpinyingeneration    = True   # Should we try and write readings and measure words that include colorized pinyin? True or False
meaninggeneration            = True   # Should we try and fill out a field called Meaning with the definition? True or False
fallbackongoogletranslate    = True   # Should we use Google to fill out the Meaning field if needs be? True or False
colorizedcharactergeneration = True   # Should we try and fill out a field called Color with a colored version of the character? True or False
audiogeneration              = True   # Should we try and fill out a field called Audio with text-to-speech commands? True or False
detectmeasurewords           = True   # Should we try and put measure words seperately into a field called MW? True or False

# Should we give each translation entry a number? Uncomment the line showing how you would like them to be numbered:
numbermeanings = [u"㊀", u"㊁", u"㊂", u"㊃", u"㊄", u"㊅", u"㊆", u"㊇", u"㊈", u"㊉", u"⑪", u"⑫", u"⑬", u"⑭", u"⑮", u"⑯", u"⑰", u"⑱", u"⑲", u"⑳"]  # Cute Chinese symbols for first 10, then english up to 20
#numbermeanings = [u"①", u"②", u"③", u"④", u"⑤", u"⑥", u"⑦", u"⑧", u"⑨", u"⑩", u"⑪", u"⑫", u"⑬", u"⑭", u"⑮", u"⑯", u"⑰", u"⑱", u"⑲", u"⑳"]      # Pretty bubble-numerals
#numbermeanings = []           # use simple "(1)", "(2)", "(3)", "(4)", "(5)" ...
#numbermeanings = None         # do not give each entry a number

# Seperator for meaning dictionary entries. Uncomment the one you want or add your own:
meaningseperator = "<br />"
#meaningseperator = ", "
#meaningseperator = "; "
#meaningseperator = " | "

# Prefer simplified or traditional characters? This will be used when formatting meanings with embedded Hanzi and measure words.
prefersimptrad = "simp"
#prefersimptrad = "trad"

# What type of audio files are you using? List in descending order of priority (default is prefer ".ogg" and dislike ".wav"]
audioextensions = [".ogg", ".mp3", ".wav"]

# Source location for Mandarin auidio files download
# You should not have to change this setting as it defaults to a free and usable sound-set.
# Be aware that you may be able to find higher quality audio files from other sources.
mandarinsoundsurl = "http://www.chinese-lessons.com/sounds/Mandarin_sounds.zip"
# TODO: these files contain some problem file names that do not match the pinyin standard.
# For example "me.mp3" instead of "me5.mp3" or "me4.mp3" - need to find a way to fix this.


### Color Settings ####

# You can change the colors PyKit uses to format tones and text with.

# Remember: Just because you can change something doesn't mean you should! :)
# If you use non-standard tone colorization you may become 'weird'
# Other applications may not let you use your non-standard colors
# These also have the benefit of following the colors of the rainbow, awww...

colorlist = {
#   | Tone colors |
    1 : u"#ff0000",     # 1st tone color, default is #FF0000 (red)
    2 : u"#ffaa00",     # 2nd tone color, default is #ffaa00 (orange)
    3 : u"#00aa00",     # 3rd tone color, default is #00aa00 (green)
    4 : u"#0000ff",     # 4th tone color, default is #0000FF (blue)
    5 : u"#545454",     # 5th tone color, default is #545454 (grey)

#   | User colors |
    6 : u"#00AAFF",     # default is #000000, black [not the same as 'no color']
    7 : u"#55007F",     # default is #55007F, yellow
    8 : u"#FF00FF",     # default is #FF00FF, pink
    9 : u"#000000",      
    10: u"#000000",      
    11: u"#000000",      
    12: u"#000000"}

### Field Settings ###

# These are prioritised lists which encode what kind of field is given what name in the model.
# Leftmost field names are given priority over any others later in the list.
# You should not have to remove or replace any entry, simply add your entry on the right hand side.
candidateFieldNamesByKey = {
    'expression' : ["Expression", "Hanzi", "Chinese", u"汉字", u"中文"],
    'reading'    : ["Reading", "Pinyin", "PY", u"拼音"],
    'meaning'    : ["Meaning", "Definition", "English", "German", "French", u"意思", u"翻译", u"英语", u"法语", u"德语"],
    'audio'      : ["Audio", "Sound", "Spoken", u"声音"],
    'color'      : ["Color", "Colour", "Colored Hanzi", u"彩色"],
    'mw'         : ["MW", "Measure Word", "Classifier", u"量词"]
  }

# The following line controls which model tag is used (it must match your deck).
# You should not need to change this setting.
modelTag = "Mandarin"


############### End of Settings Section ###############

if __name__ != "__main__":
    import sys

    import pinyin.anki.main as main
    from ankiqt import mw
        
    # Save a reference to the toolkit onto the mw, preventing garbage collection of PyQT objects
    mw.pinyintoolkit = main.PinyinToolkit(mw, sys.modules[__name__]).installhooks()
else:
    print "This is a plugin for the Anki Spaced Repition learning system and cannot be run directly."
    print "Please download Anki from <http://ichi2.net/anki/>"
