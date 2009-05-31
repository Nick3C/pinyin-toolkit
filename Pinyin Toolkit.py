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

# Where we can download the Mandarin sounds from.
# You should not have to change this setting:
mandarinsoundsurl = "http://www.chinese-lessons.com/sounds/Mandarin_sounds.zip"

### Field Settings ###

# These are prioritised lists which encode what kind of field is given what name in the model.
# Leftmost field names are given priority over any others later in the list.
candidateFieldNamesByKey = {
    'expression' : ["Expression", "Hanzi"],
    'reading'    : ["Reading", "Pinyin"],
    'meaning'    : ["Meaning", "Definition"],
    'audio'      : ["Audio", "Sound", "Spoken"],
    'color'      : ["Color", "Colour", "Colored Hanzi"],
    'mw'         : ["MW", "Measure Word"]
  }

# The following line controls which model tag is used (it must match your deck)
# You should not need to change this setting
modelTag = "Mandarin"

############### End of Settings Section ###############

import os
import getpass

from PyQt4 import QtGui, QtCore

from ankiqt import mw
from ankiqt.ui import utils

import anki
from anki.hooks import addHook, removeHook
from anki.features.chinese import onFocusLost as oldHook

from pinyin import pinyin, transformations, dictionary, google, media, utils


# Global dictionary instance for the language under consideration
needmeanings = meaninggeneration or detectmeasurewords
dictionary = dictionary.PinyinDictionary.load(dictlanguage, needmeanings=needmeanings)

# Discover the available sound files:
try:
    available_media = {}
    
    # Media comes from two sources:
    #  1) Media just copied into the media directory by the user. We detect this by looking
    #     at the filename. If it is in the format foo5.extension then it is a candidate sound.
    if mw.deck.mediaDir():
        # An accessible mediaDir exists - look through it for files
        available_media.update(dict([(filename, filename) for filename in os.listdir(mw.deck.mediaDir())]))
        
    #  2) Media imported into the media directory by Anki. We detect this by consulting the media
    #     database and looking for files whose original path had the foo5.extension format.
    for orig_path, filename in mw.deck.s.all("select originalPath, filename from media"):
        # Note that originalPath is a FULL path so need to call os.path.basename on it
        available_media[os.path.basename(orig_path)] = filename
except IOError:
    available_media = {}


def chooseField(candidateFieldNames, fact):
    # Find the first field that is present in the fact
    for candidateField in candidateFieldNames:
        if candidateField in fact.keys():
            return candidateField
    
    # No suitable field found!
    return None


# Install hook into focus event of Anki: we regenerate the model information when
# the cursor moves off the Expression field
def onFocusLost(fact, field):
    # Have we just moved off the expression field in a Mandarin model?
    expressionField = chooseField(candidateFieldNamesByKey['expression'], fact)
    if field.name != expressionField or not(anki.utils.findTag(modelTag, fact.model.tags)):
        return
    
    # Update the card, ignoring any errors
    utils.suppressexceptions(lambda: updatefact(fact, field.value))

removeHook('fact.focusLost', oldHook)
addHook('fact.focusLost', onFocusLost)


# Install menu item that will allow downloading of the sounds
def downloadAndInstallSounds():
    # Download ZIP, using cache if necessary
    the_media = media.MediaDownloader().download(mandarinsoundsurl,
                                                 lambda: utils.showInfo("Downloading the sounds - this might take a while!"))
    
    # Install each file from the ZIP into Anki
    the_media.extractand(mw.deck.addMedia)
    
    # Tell the user we are done
    exampleAudioField = candidateFieldNamesByKey['audio'][0]
    utils.showInfo("Finished installing Mandarin sounds! To use them, make sure you have "
                   + "an " + exampleAudioField + " field and a substitution %(" + exampleAudioField + ")s in your model")

action = QtGui.QAction('Download Mandarin sound samples', mw)
action.setStatusTip('Download and install the Mandarin sound samples into this deck')
action.setEnabled(True)

mw.connect(action, QtCore.SIGNAL('triggered()'), downloadAndInstallSounds)
mw.mainWin.menuTools.addAction(action)


# Install menu item that will allow filling of missing information
def suitableCards(deck):
    for model in deck.models:
        if anki.utils.findTag(modelTag, model.tags):
            card_model = deck.s.scalar('select id from cardmodels where modelId = %s' % model.id)
            for card in deck.s.query(anki.cards.Card).filter('cardModelId = %s' % card_model):
                yield card

def fillMissingInformation():
    for card in suitableCards(mw.deck):
        expressionField = chooseField(candidateFieldNamesByKey['expression'], card.fact)
        updatefact(card.fact, card.fact[expressionField])
    
    utils.showInfo("Finished filling in missing information")

action = QtGui.QAction('Fill all missing Mandarin information', mw)
action.setStatusTip('Update all the cards in the deck with any missing information the Pinyin Toolkit can provide')
action.setEnabled(True)

mw.connect(action, QtCore.SIGNAL('triggered()'), fillMissingInformation)
mw.mainWin.menuTools.addAction(action)


# Tell Anki about the plugin
mw.registerPlugin("Mandarin Chinese Pinyin Toolkit", 4)


# The function the hook uses to actually do the update:
def updatefact(fact, expression):
    # Discover the final field names
    fieldNames = dict([(key, chooseField(candidateFieldNames, fact)) for key, candidateFieldNames in candidateFieldNamesByKey.items()])
    
    # If there is no expression, zero every field
    if fieldNames['expression'] != None and not(fact[fieldNames['expression']]):
        for key in ["reading", "meaning", "color", "mw"]:
            if fieldNames[key] != None:
                fact[fieldNames[key]] = u""
            
        # DEBUGME - add a more rigorous check on audio fields here (having problems with ratio based approach)
        audioField = fieldNames['audio']
        if audioField != None and len(fact[audioField]) < 40:
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
        current_reading = transformations.Colorizer().colorize(reading)
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
            'reading' : (True,                         lambda: pinyin),
            'meaning' : (meaninggeneration,            lambda: formatmeanings([meaning for meaning in meanings if detectmeasurewords or measurewordmeaning(meaning) == None])),
            'mw'      : (detectmeasurewords,           lambda: formatmeasureword([measurewordmeaning(meaning) for meaning in meanings if measurewordmeaning(meaning)])),
            'audio'   : (audiogeneration,              lambda: transformations.PinyinAudioReadings(available_media, audioextensions).audioreading(reading)),
            'color'   : (colorizedcharactergeneration, lambda: transformations.Colorizer().colorize(dictionary.tonedchars(expression)).flatten())
        }
    
    for key, (enabled, updater) in updaters.items():
        # Skip updating if no suitable field, we are disabled, or the field has text
        fieldName = fieldNames[key]
        if fieldName == None or not(enabled) or fact[fieldName].strip() != '':
            continue
        
        # Update the value in that field
        value = updater()
        if value != None and value != fact[fieldName]:
            fact[fieldName] = value

# Allows us to detect measure words meanings
def measurewordmeaning(meaning):
    if meaning.startswith("CL:"):
        return meaning[3:].replace("["," - ").replace("]","")
    else:
        return None


if __name__ == "__main__":
  print "This is a plugin for the Anki Spaced Repition learning system and cannot be run directly."
  print "Please download Anki from <http://ichi2.net/anki/>"