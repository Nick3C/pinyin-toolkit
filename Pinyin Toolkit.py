#!/usr/bin/env python
# -*- coding: utf-8 -*-
########################################################################
###                   Mandarin-Chinese Pinyin Toolkit                ### 
########################################################################
# A Plugin for the Anki Spaced Repition learning system <http://ichi2.net/anki/>

# Version Details:
pinyin_toolkit="0.05 dev 4.3"
CCDict_Ver="2009-05-29T05:46:28Z" # [n=84885] http://www.mdbg.net/chindict/chindict.php?page=cc-cedict
HanDeDict_Ver="Sat May 30 00:20:38 2009" # [n=169500] http://www.chinaboard.de/chinesisch_deutsch.php?mode=dl&w=8
CFDICT_Ver="Wed Jan 21 01:49:53 2009" # [n=593] http://www.chinaboard.de/fr/cfdict.php?mode=dl&w=8
dictlanguage="en" # Sets language
# full support for: "en" (english) and "de" (German)
#     Note that there are some important differences between handedict and cc-cedict (Measures Words, Simp-Trad swap, etc)
# partial support for: "fr" (French) [CFDICT is still small but google translate will pick up the slack]
# google translate support for other languges (use language code: http://www.loc.gov/standards/iso639-2/php/code_list.php)

############### Settings Section ###############

### Options ###

# Should we output tone marks rather than numbers on pinyin? True or False
tonify                       = True
# Should we try and write readings that include colorized pinyin? True or False
colorizedpinyingeneration    = True
# Should we try and fill out a field called Meaning with the definition? True or False
meaninggeneration            = True
# Should we use Google to fill out the Meaning field if needs be? True or False
fallbackongoogletranslate    = False
# Should we try and fill out a field called Color with a colored version of the character? True or False
colorizedcharactergeneration = True
# Should we try and fill out a field called Audio with text-to-speech commands? True or False
audiogeneration              = True
# Should we try and put measure words seperately into a field called MW? True or False
detectmeasurewords           = True

# Should we number meanings? True or False
numbermeanings   = True
# Seperator for meaning dictionary entries. Uncomment the one you want or add your own:
meaningseperator = "<br />"
#meaningseperator = ", "
#meaningseperator = "; "

# What type of audio files are you using? List in descending order of priority
audioextensions = [".mp3", ".ogg", ".wav"]

### Field Settings (must match your model) ###

expressionField = "Expression"
readingField    = "Reading"
meaningField    = "Meaning"
audioField      = "Audio"
colorField      = "Color"
mwField         = "MW"

# The following line controls which model tag is used (it must match your deck)
# You should not need to change this setting
modelTag = "Mandarin"

############### End of Settings Section ###############

import os

from ankiqt import mw
from ankiqt.ui import utils

import anki
from anki.hooks import addHook, removeHook
from anki.features.chinese import onFocusLost as oldHook

from pinyin import pinyin, transformations, dictionary, google


# Global dictionary instance for the language under consideration
needmeanings = meaninggeneration or detectmeasurewords
dictionary = dictionary.PinyinDictionary.load(dictlanguage, needmeanings=needmeanings)

# Discover the available sound files:
try:
    available_media = os.listdir(mw.deck.mediaDir())
except IOError:
    available_media = []


# Install hook into focus event of Anki: we regenerate the model information when
# the cursor moves off the Expression field
def onFocusLost(fact, field):
    # Have we just moved off the expression field in a Mandarin model?
    if field.name != expressionField or not(anki.utils.findTag(modelTag, fact.model.tags)):
        return
    
    # Update the card, ignoring any errors
    try:
        updatefact(fact, field.value)
    except:
        pass

removeHook('fact.focusLost', oldHook)
addHook('fact.focusLost', onFocusLost)
mw.registerPlugin("Mandarin Chinese Pinyin Toolkit", 4)


# The function the hook uses to actually do the update:
def updatefact(fact, expression):
    # If there is no expression, zero every field
    if not fact[expressionField]:
        fact[readingField] = u""
        fact[meaningField] = u""
        fact[colorField] = u""
        # DEBUGME - add a more rigorous check on audio fields here (having problems with ratio based approach)
        if len(fact[audioField]) < 40:
            fact[audioField] = u""
    
    # Figure out the reading for the expression field
    reading = dictionary.reading(expression)
    
    # Preload the meaning, but only if we absolutely have to
    if needmeanings:
        meanings = dictionary.meanings(expression)
        # If the dictionary can't answer our question, ask Google Translate
        if meanings == None and fallbackongoogletranslate:
            meanings = googletranslate(expression, dictlanguage)
    
    # Generate the pinyin - we're always going to need it
    if colorizedpinyingeneration:
        current_reading = transformations.PinyinColorizer().colorize(reading)
    else:
        current_reading = reading
    
    pinyin = current_reading.flatten(tonify=tonify)
    
    # Define how we are going to format the meaning field:
    def formatmeanings(meanings):
        if numbermeanings:
            meanings = ["(" + str(n + 1) + ") " + meaning for n, meaning in enumerate(meanings)]
    
        return meaningseperator.join(meanings)
    
    # Define how we are going to format the measure word field:
    def formatmeasureword(measurewords):
        if len(measurewords) == 0:
            # No measure word, so don't update the field
            return None
        else:
            # Just use the first measure word meaning, if there was more than one
            return measurewords[0]
    
    # Do the updates on the fields the user has requested:
    updaters = {
            readingField : (True,                         lambda: pinyin),
            meaningField : (meaninggeneration,            lambda: formatmeanings([meaning for meaning in meanings if detectmeasurewords or measurewordmeaning(meaning) == None])),
            mwField      : (detectmeasurewords,           lambda: formatmeasureword([measurewordmeaning(meaning) for meaning in meanings if measurewordmeaning(meaning)])),
            audioField   : (audiogeneration,              lambda: transformations.PinyinAudioReadings(available_media, audioextensions).audioreading(reading)),
            colorField   : (colorizedcharactergeneration, lambda: transformations.CharacterColorizer().colorize(reading).flatten())
        }
    
    for fieldname, (enabled, updater) in updaters.items():
        if enabled and (fieldname in fact.keys()):
            value = updater()
            if value != None and value != fact[fieldname]:
                fact[fieldname] = value

# Allows us to detect measure words meanings
def measurewordmeaning(meaning):
    if meaning.startswith("CL:"):
        return meaning[3:].replace("["," - ").replace("]","")
    else:
        return False


if __name__ == "__main__":
  print "This is a plugin for the Anki Spaced Repition learning system and cannot be run directly."
  print "Please download Anki from <http://ichi2.net/anki/>"