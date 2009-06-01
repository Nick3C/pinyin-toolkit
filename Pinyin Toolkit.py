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
pinyin_toolkit="0.05 dev"

CCDict_Ver="2009-05-29T05:46:28Z" # [n=84885] http://www.mdbg.net/chindict/chindict.php?page=cc-cedict
HanDeDict_Ver="Sat May 30 00:20:38 2009" # [n=169500] http://www.chinaboard.de/chinesisch_deutsch.php?mode=dl&w=8
CFDICT_Ver="Wed Jan 21 01:49:53 2009" # [n=593] http://www.chinaboard.de/fr/cfdict.php?mode=dl&w=8
# Note that these dictionaries are not identical and have important formatting differences and field order variation

############  Language Masterswitch  ############
# The following option controls the language used for translation and dictionary lookup.
dictlanguage="en"

# Note that best results occur when Pinyin Toolkit is used with a local dictionary and online support
# Full support:     "en" (english)    "de" (German)
# Hybrid-support:   "fr" (French)     [the CFDICT is still in its infancy]
# Partial-support:   (all other language)

# Codes for partial supported languages can be found here: http://www.loc.gov/standards/iso639-2/php/code_list.php
# Do not change to another full/hybrid support language without downloading the dictionary or you will break local lookup.

############### Settings Section ###############

### Options ###

tonify                       = True   # Should we output tone marks rather than numbers on pinyin? True or False
colorizedpinyingeneration    = True   # Should we try and write readings that include colorized pinyin? True or False
meaninggeneration            = True   # Should we try and fill out a field called Meaning with the definition? True or False
fallbackongoogletranslate    = True   # Should we use Google to fill out the Meaning field if needs be? True or False
colorizedcharactergeneration = True   # Should we try and fill out a field called Color with a colored version of the character? True or False
audiogeneration              = True   # Should we try and fill out a field called Audio with text-to-speech commands? True or False
detectmeasurewords           = True   # Should we try and put measure words seperately into a field called MW? True or False

# Should we give each meaning a number? Uncomment the line showing how you would like them to be numbered:
numbermeanings = [u"㊀", u"㊁", u"㊂", u"㊃", u"㊄", u"㊅", u"㊆", u"㊇", u"㊈", u"㊉", u"⑪", u"⑫", u"⑬", u"⑭", u"⑮", u"⑯", u"⑰", u"⑱", u"⑲", u"⑳"]
#numbermeanings = [u"①", u"②", u"③", u"④", u"⑤", u"⑥", u"⑦", u"⑧", u"⑨", u"⑩", u"⑪", u"⑫", u"⑬", u"⑭", u"⑮", u"⑯", u"⑰", u"⑱", u"⑲", u"⑳"]
#numbermeanings = True         # use simple "(1)", "(2)", "(3)", "(4)", "(5)" ...
#numbermeanings   = False      # do not give each entry a number

# Seperator for meaning dictionary entries. Uncomment the one you want or add your own:
meaningseperator = "<br />"
#meaningseperator = ", "
#meaningseperator = "; "
#meaningseperator = " | "

# Prefer simplified or traditional characters? (for very limited circumstances such as when checking measure words)
prefersimptrad = "simp"
#prefersimptrad = "trad"

# What type of audio files are you using? List in descending order of priority (default is prefer ".ogg" and dislike ".wav"]
audioextensions = [".ogg", ".mp3", ".wav"]

# Source location for Mandarin auidio files download
# You should not have to change this setting as it defaults to a free and usable sound-set.
# Be aware that you may be able to find higher quality audio files from other sources.
mandarinsoundsurl = "http://www.chinese-lessons.com/sounds/Mandarin_sounds.zip"


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
    'mw'         : ["MW", "Measure Word", u"量词"]
  }

# The following line controls which model tag is used (it must match your deck).
# You should not need to change this setting.
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

from pinyin import pinyin, transformations, dictionary, dictionaryonline, media, utils

# Test internet connectivity by performing a gTrans call
# If this call fails then translations are disabled until Anki is restarted
# This prevents a several second delay from occuring when chaging field with no internet
if (fallbackongoogletranslate):
    fallbackongoogletranslate = dictionaryonline.gCheck(u'这是一个网络试验',dictlanguage)

# Global dictionary instance for the language under consideration
needmeanings = meaninggeneration or detectmeasurewords
dictionary = dictionary.PinyinDictionary.load(dictlanguage, needmeanings=needmeanings)

# Discover the available sound files:
try:
    available_media = {}
    
    # Media comes from two sources:
    #  1) Media copied into the media directory by the user. We detect this by looking
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
# the cursor moves from the Expression field to another field
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
    utils.showInfo("Finished installing Mandarin sounds! These sound files will be used automatically as long as you have "
                   + " the: <b>" + exampleAudioField + "</b> field in your deck, and the text: <b>%(" + exampleAudioField + ")s</b> in your card template")

action = QtGui.QAction('Download Mandarin text-to-speech Audio Files', mw)
action.setStatusTip('Download and install a sample set of Mandarin audio files into this deck. This will enable automatic text-to-speech.')
action.setEnabled(True)
# note that these files contain some problem file names that do not match the pinyin standard. For example "me.mp3" instead of "me5.mp3" or "me4.mp3"

mw.connect(action, QtCore.SIGNAL('triggered()'), downloadAndInstallSounds)
mw.mainWin.menuTools.addAction(action)

# DEBUG - I think these should really be moved to advanced. They aren't going to be run very often and will get in the way. (let's not make Damien complain :)
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
    
    utils.showInfo("All missing information has been successfully added to your deck.")

action = QtGui.QAction('Fill all missing card data using Pinyin Toolkit', mw)
# DEBUG consider future feature to add missing measure words cards after doing so (not now)
action.setStatusTip('Update all the cards in the deck with any missing information the Pinyin Toolkit can provide.')
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
            
        # DEBUG Me - Auto generated pinyin should be at least "[sound:" + ".xxx]" (12 characters) plus pinyin (max 6). i.e. 18
        # DEBUG - Split string around "][" to get the audio of each sound in an array. Blank the field unless any one string is longer than 20 characters
        # Exploit the fact that pinyin text-to-speech pinyin should be no longer than 18 characters to guess that anything longer is user generated
        audioField = fieldNames['audio']
        if audioField != None and len(fact[audioField]) < 40:
            fact[audioField] = u""
    
    # Figure out the reading for the expression field
    reading = dictionary.reading(expression)
    
    # Preload the meaning, but only if we absolutely have to
    if needmeanings:
        meanings = dictionary.meanings(expression)
        # If the dictionary can't answer our question, ask Google Translate
        # If there is a long word followed by another word then this will be treated as a phrase
        # Phrases are also queried using googletranslate rather than the local dictionary
        # This helps deal with small dictionaries (for example French)
        if meanings == None and fallbackongoogletranslate:
            meanings = dictionaryonline.gTrans(expression, dictlanguage)
    
    # Generate the pinyin - we're always going to need it
    if colorizedpinyingeneration:
        current_reading = transformations.Colorizer().colorize(reading)
    else:
        current_reading = reading
    
    pinyin = current_reading.flatten(tonify=tonify).lower() # Put pinyin into lowercase before anything is done to it
    
    # Define how we are going to format the meaning field (if at all)
    def formatmeanings(meanings):
        if len(meanings)>1:
            if not numbermeanings == False:
                if numbermeanings == True:
                    meanings = ["(" + str(n + 1) + ") " + meaning for n, meaning in enumerate(meanings)]
                else:
                    meanings = [ numbermeanings[n] + " "  + meaning for n, meaning in enumerate(meanings)]   
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

# Allows us to detect measure word data from dictionary
# Currently only English CC-CEDICT support this function
def measurewordmeaning(meaning):
    # DEBUG - every dictionary entry should replace "CL:" with "MW:" even if this option is off; MW at least meaning something.
    # DEBUG - If this works (i.e. paste into MW field) then the "CL:" line should be cut from the translation entry (otherwise we have duplication) 
    # DEBUG - f this works then there should be no number "(2)" for this line [and none at all if total lines was only 2
    if meaning.startswith("CL:"):
        # use a for loop to go through each reading entry to collect any starting with "CL:", cut into an array
        # go through the array here with each of the MW lines
        # DEBUG - need a fix for some CC-CEDICT lines that are formatted "CL:[char1],[char2],[char3]" but this is not common and not very important

        # chose either simplified or traditional measure word based on preferences
        # somewhat complex format of this statement allows for easy inclusion of other dictionaries in the future
        MWposdiv = meaning.find("|")
        if dictlanguage =="en":
            if prefersimptrad == "simp":
                MWpoststart = MWposdiv - 1            
            elif prefersimptrad == "trad":
                MWposstart = MWposdiv + 1
            MWposend=MWposstart+1
            MWentry = meaning[MWposstart:MWposend] + meaning[MWposdiv+2:] # cut measure word as per selection and add to pinyin         
        else:
            MWentry = meaning
        mwaduio = " [sound:MW]" # DEBUG - pass to audio loop
        MWentry = MWEntr.replace("["," - ").replace("]","") + mwaduio
        
        return MWentry
    else:
        return None


if __name__ == "__main__":
  print "This is a plugin for the Anki Spaced Repition learning system and cannot be run directly."
  print "Please download Anki from <http://ichi2.net/anki/>"