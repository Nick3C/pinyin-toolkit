#!/usr/bin/python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
########################################################################
###                   Mandarin-Chinese Pinyin Toolkit                ### 
########################################################################
# A Plugin for the Anki Spaced Repition learning system <http://ichi2.net/anki/>

# Version Details:
pinyin_toolkit="0.04"
CCDict_Ver="2009-05-16T00:23:12Z"
HanDeDict_Ver="Sat May 16 00:16:20 2009"
dictlanguage="German" # Sets dictionary to be used

"""
This plugin adds several useful features for Mandarin decks:
1 improved pinyin generation using a dictionary to guess the likely reading
2 output tone marks instead of numbers
3 colorize pinyin according to tone mark to assist visual learners
4 look up the meaning of characters in English (or German in the German edition)
(5) colorize character according to tone to assist visual learners [if enabled]
(6) generate the appropriate "[sound:ni2.ogg][sound:hao3.ogg]" tags to give rudimentary text-to-speech [if enabled]

The plugin replaces standard Mandarin generation, so there is no need to rename your model or model tags.
Features 1 to 4 will work automatically out of the box. Features 5 and 6 are optional extras that require enabling.

"""
# Installation
"""
1) download using Anki shared-plugin download feature
2) Ensure your model has the tag "Mandarin"
3) Ensure your model has the fields "Expression", "Reading", and "Meaning" (or customise below)
4) To active character colorization:
  - ensure your model has a field called "Color" to populate with colored characters 
  - edit your models to use the new field
  - The best way to do this is test on plain characters, but show colored characters in answers or where you are not testing reading or tones. 
5) To active sound tag generation:
  - ensure your model has a field called "Audio"
  - obtain audio files in the format "ni3.ogg", "hao3.ogg"
  - you can download such files here http://www.chinese-lessons.com/download.htm
  - note that commercial software (such as Wenlin) includes higher quality versions you can use
  - place the files in your deck's media directory (keep a copy, as Anki wipes them in media checks)

If you plan not to use features such as character colorisation or audio generation,
you should turn them off in the settings section below.

"""
# Changelog

# Version 0.04 (19/05/2009)  Nick Cook <nick@n-line.co.uk>  [http://www.n-line.co.uk]
"""
* Two versions are now being distributed: English (using CC-CEDICT) and German (using HanDeDict)
   - Thanks to Rainer Menes for suggesting use of HanDeDict
* New character colorization feature
   - If enabled, colored hanzi will be generated and placed in a field called "Color"
   - to get the benefit of this you should alter models in a way to make use of colored Hanzi
* Fix to give better handle the formatting of dictionary entries
   - customisable dictionary meaning separator (defaults to line break)
* more reliable sound tag generation
* automatic blanking feature if hanzi field is emptied and de-focused (makes input faster)
   - audio field is ignored if longer than 40 characters (i.e. if Anki has improved or recorded audio) [a better way to do this is in the works]
* strip html from expression field before doing anything (prevents formating bugs)
* several minor fixes and improvements to general usage
- 
"""
# Version 0.03[r] (12/05/2009)  Nick Cook <nick@n-line.co.uk>  [http://www.n-line.co.uk]
"""
* Simplified and traditional generation now happens each lookup (no need to chose one or the other)
* automatic English generation from dictionary
  - English will only be generated for exact matches (words) not phrases
* automatic colorization of pnyin by tone
* Text-to-speech feature (automatic auto generation)
* support for turning off new features
* tidy code (remove unused & rationalise messy bits)
* update dictionary to latest CC-CEDICT
  - fix bug from 谁 [actually bug is no longer relevant under new directory structure]
  - fix problems with pinyin generation of "v"/"u:"
* rearrange to more logical filenames (pinyinfetcher.py etc)
* change dictionary structure for better management, easier updates, and to allow new features
   - split dictionary into 3 parts (CC-CEDICT, supplementary, and user) [entries prioritised from latter to former]
   - supplementary dictionary contains previously hard-coded entries and new data such as numbers
"""
# Version 0.02.5[r] (21/03/2009)   Nick Cook <nick@n-line.co.uk>   [http://www.n-line.co.uk]
"""
* Dictionary updated to use adapted version of CC-CEDICT
* entries increasing from 44,783 to 82,941
"""
# Version 0.02[r] (03/2009)   Damien Elmes  [http://ichi2.net/]
"""
* Ported to Anki 0.9.9.6 and tidied up
* Brian Vaughan no longer maintaing plugin
"""
# Version 0.01[r] (2008)    Brian Vaughan [http://brianvaughan.net]
"""
* Original release

"[r]" means "Retroactive Version Number"

Chinese-English CC-CEDICT, available at: <http://www.mdbg.net/chindict/chindict.php?page=cc-cedict>
Licensing of CC-CEDICT is Creative Commons Attribution-Share Alike 3.0 <http://creativecommons.org/licenses/by-sa/3.0/>

Chinese-German dictionary HanDeDict, available at: <http://www.chinaboard.de/chinesisch_deutsch.php?mode=dl&amp;sid=dd1ddd9fb952eb74300d3fd743394799&w=8>
Licensing of HanDeDict is  Creative Commons Attribution-Share Alike 2.0 Germany <http://creativecommons.org/licenses/by-sa/2.0/de/>

Previous versions of this plugin used an adapted version of the original cedict dictionary
"""
# Bug-Hunting To-Do-List & Future Development Plans
"""
Bugs & Tweaks
- track down the bug that means character colorisation fails if audio generation off 
- remove space at the end of colored pinyin [requires complex string manipulation]
- remove space between punctuation in pinyin (functional result of way colored characters are produced)
- remove the space between erhua "r" and main word in colored pinyin
- prevent loss of punctuation when colorizing characters [a lot trickier than it sounds]
- track down why HanDeDict doesn't always retrieve entries that are known to be there

Future Feature List
- bundle audio files with plugin
- (check if audio file exists before putting in tag)
- investigate Anki source to see if possible: import audio files from another directory (would solve check media wiping and make bundling audio simpler)
- look at the "Allows numbers to match pinyin tone mark.pyc" plugin, seems much more efficient tone mark generation
- English dictionary - add "(1)" "(2)" "(3)" instead of simple line spaces
- where dictionary has measure words, automatically add them to a MW field and add "noun" to "Type" field
- where dictionary contains "to " automatically ass "verb" to a field called "Type"
- rewrite code to use a less complicated class and sub structure
- rewrite code to perform a single dictionary search and assign to an array in the form: "word", "pinyin", "tones", "translation"
- add a true pinyin mode and option switch (no breaks between sylabels in same words) [this will require a full index, as above]
- change text parser to look for text in "/ /" and "[ ]" instead of using splits, there is a neat re.compile around somewhere for this

"""
############### Settings Section ###############

### Options ###
# Can be either True or False
colorizePY=True 
tonify=True
dictionarygeneration=True
cochargen=True
audiogen=True

# seperator for meaning dictionary entries
endictsep = "<br />"
# default is "<br />" obvious alternatives are: ", " or "; "

# What type of audio files are you using?
audioextension = ".mp3" 

### Field Settings (must match your model) ###

expressionField = "Expression"
readingField = "Reading"
meaningField ="Meaning"
audioField = "Audio"
colorField = "Color"

# The following line controls which model tag is used (it must match your deck)
# You should not need to change this setting
modelTag = "Mandarin"

############### End of Settings Section ###############

import sys
import os

import re
from ankiqt import mw
import anki
from pinyin import pinyinfetcher
from anki.hooks import addHook, removeHook
from anki.features.chinese import onFocusLost as oldHook

#define the convertor models as per options above
converterPY = pinyinfetcher.PinyinFetcher(colorizePY,tonify)

if(dictionarygeneration):
    converterENG = pinyinfetcher.PinyinFetcher(False,False,True,False,endictsep,dictlanguage)
else:
    converterENG = None
    
if(audiogen):
    converterAudio = pinyinfetcher.PinyinFetcher(False,False,False,True)
else:
    converterAudio = None

if(cochargen):
    converterColChar = pinyinfetcher.PinyinFetcher(True)
else:
    converterColChar = None  
    
def onFocusLost(fact, field):
    if field.name != expressionField:
        return
    if not anki.utils.findTag(modelTag, fact.model.tags):
        return
    try:
        if not fact[expressionField]:
            fact[readingField] = u""
            fact[meaningField] = u""
            fact[colorField] = u""
            audiolen=len(fact[audioField])
            # DEBUGME - add a more rigerous check on audio fields here (having problems with ratio based approach)
            if audiolen < 40: #
                fact[audioField] = u""
        if not fact[readingField] :
            tmp = converterPY.getPinyin(field.value,False)
            if tmp != field.value:
                fact[readingField] = tmp.lower()
        if not fact[meaningField]:
            tmp = converterENG.getPinyin(field.value,True)
            if tmp != field.value:
                fact[meaningField] = tmp
        if not fact[audioField]:
            tmp = converterAudio.getPinyin(field.value,False,False,False,audioextension)
            if tmp != field.value:
                fact[audioField] = tmp.lower()
        if not fact[colorField]:
            tmp = converterColChar.getPinyin(field.value,False,True)
            if tmp != field.value:
                fact[colorField] = tmp 
        return
    except:
        return 
    
removeHook('fact.focusLost', oldHook)
addHook('fact.focusLost', onFocusLost)
mw.registerPlugin("Mandarin Chinese Pinyin Toolkit", 4)


if __name__ == "__main__":
  print "This is a plugin for the Anki Spaced Repition learning system and cannot be run directly."
  print "Please donwload Anki from <http://ichi2.net/anki/>"