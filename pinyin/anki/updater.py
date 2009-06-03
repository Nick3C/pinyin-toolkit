#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from pinyin import dictionary, dictionaryonline, media, meanings, pinyin, transformations
from pinyin.logger import log

import utils

class FieldUpdater(object):
    def __init__(self, mw, notifier, config, dictionary):
        self.mw = mw
        self.notifier = notifier
        self.config = config
        self.dictionary = dictionary
    
    def preparetokens(self, tokens):
        if self.config.colorizedpinyingeneration:
            tokens = transformations.Colorizer(self.config.colorlist).colorize(tokens)
    
        return tokens.flatten(tonify=self.config.tonify)
    
    #
    # Media discovery
    #
    
    def discoverlegacymedia(self):
        # NB: we used to do this when initialising the toolkit, but that dosen't work,
        # for the simple reason that if you change deck the media should change, but
        # we can't hook that event
        
        # Discover all the files in the media directory
        mediaDir = self.mw.deck.mediaDir()
        if mediaDir:
            try:
                mediadircontents = os.listdir(mediaDir)
            except IOError:
                log.exception("Error while listing media directory")
                mediadircontents = None
        else:
            log.info("The media directory was either not present or not accessible")
            mediadircontents = None
        
        # Finally, find any legacy media in that directory. TODO: use this method for something
        return media.discoverlegacymedia(mediadircontents, self.mw.deck.s.all("select originalPath, filename from media"))
    
    #
    # Generation
    #
    
    def generatereading(self, dictreading):
        # TODO: do we really want lower case here? If so, we should do it for colorized pinyin as well.
        return self.preparetokens(dictreading).lower() # Put pinyin into lowercase before anything else is done to it
    
    def generateaudio(self, notifier, dictreading):
        mediapacks = media.MediaPack.discover()
        if len(mediapacks) == 0:
            # Show a warning the first time we detect that we're missing a sound pack
            notifier.infoOnce("We appear to be missing some audio samples. This might be our fault, but if you haven't already done so, "
                              + "please use 'Tools' -> 'Download Mandarin text-to-speech Audio Files' to install the samples. Alternatively, "
                              + "you can disable the text-to-speech functionality in the Pinyin Toolkit settings.")
            
            # There is no way we can generate an audio reading with no packs - give up
            return None
        
        # Get the best media pack to generate the audio, along with the string of files from that pack we need to take
        mediapack, output, _mediamissing = transformations.PinyinAudioReadings(mediapacks, self.config.audioextensions).audioreading(dictreading)
        
        # Construct the string of audio tags from the optimal choice of sounds
        output_tags = u""
        for outputfile in output:
            # Install required media in the deck as we go, getting the canonical string to insert into the sound field upon installation
            output_tags += "[sound:%s]" % self.mw.deck.addMedia(os.path.join(mediapack.packpath, outputfile))
        
        return output_tags
    
    def generatemeanings(self, dictmeanings):
        if dictmeanings == None or len(dictmeanings) == 0:
            # We didn't get any meanings, don't update the field
            return None
        
        # Prepare all the meanings by flattening them and removing empty entries
        meanings = [meaning for meaning in [self.preparetokens(dictmeaning) for dictmeaning in dictmeanings] if meaning.strip != '']
        
        # Don't add meaning numbers if it is disabled or there is only one meaning
        if len(meanings) > 1 and self.config.numbermeanings != None:
            def meaningnumber(n):
                if n < len(self.config.numbermeanings):
                    return self.config.numbermeanings[n]
                else:
                    # Ensure that we fall back on normal (n) numbers if there are more numbers than we have in the supplied list
                    return "(" + str(n) + ")"
        
            # Add numbers to all the meanings in the list
            meanings = [meaningnumber(n) + " " + meaning for n, meaning in enumerate(meanings)]
        
        # Splice the meaning lines together with the seperator
        return self.config.meaningseperator.join(meanings)
    
    def generatemeasureword(self, dictmeasurewords):
        if dictmeasurewords == None or len(dictmeasurewords) == 0:
            # No measure word, so don't update the field
            return None
        
        # Just use the first measure word meaning, if there was more than one
        return self.preparetokens(dictmeasurewords[0])
    
    def generatecoloredcharacters(self, expression):
        return transformations.Colorizer(self.config.colorlist).colorize(self.dictionary.tonedchars(expression)).flatten()
    
    #
    # Core updater routine
    #
    
    def updatefact(self, notifier, fact, expression):
        # Discover the final field names
        fieldNames = dict([(key, utils.chooseField(candidateFieldNames, fact)) for key, candidateFieldNames in self.config.candidateFieldNamesByKey.items()])
    
        # AutoBlanking Feature - If there is no expression, zeros relevant fields
        # DEBUG - add feature to store the text when a lookup is performed. When new text is entered then allow auto-blank any field that has not been edited
        if fieldNames['expression'] != None and not(fact[fieldNames['expression']]):
            for key in ["reading", "meaning", "color", "mw"]:
                if fieldNames[key] != None:
                    fact[fieldNames[key]] = u""
            
            # DEBUG Me - Auto generated pinyin should be at least "[sound:" + ".xxx]" (12 characters) plus pinyin (max 6). i.e. 18
            # DEBUG - Split string around "][" to get the audio of each sound in an array. Blank the field unless any one string is longer than 20 characters
            # Exploit the fact that pinyin text-to-speech pinyin should be no longer than 18 characters to guess that anything longer is user generated
            # MaxB comment: I don't think that will work, because we import the Mandarin Sounds into anki and it gives them /long/ names.  Instead, how
            # about we check if all of the audio files referenced are files in the format pinyin<tone>.mp3?
            audioField = fieldNames['audio']
            if audioField != None and len(fact[audioField]) < 40:
                fact[audioField] = u""
    
        # Figure out the reading for the expression field
        dictreading = self.dictionary.reading(expression)
    
        # Preload the meaning, but only if we absolutely have to
        if self.config.needmeanings:
            hasMeasureWordField = fieldNames["mw"] != None
            if self.config.detectmeasurewords and hasMeasureWordField:
                # Get measure words and meanings seperately
                dictmeanings, dictmeasurewords = self.dictionary.meanings(expression, self.config.prefersimptrad)
            else:
                # Get meanings and measure words together in one list
                dictmeanings = self.dictionary.flatmeanings(expression, self.config.prefersimptrad)
                dictmeasurewords = None
            
            # If the dictionary can't answer our question, ask Google Translate.
            # If there is a long word followed by another word then this will be treated as a phrase.
            # Phrases are also queried using googletranslate rather than the local dictionary.
            # This helps deal with small dictionaries (for example French)
            if dictmeanings == None and dictmeasurewords == None and self.config.fallbackongoogletranslate:
                log.info("Falling back on Google for %s", expression)
                dictmeanings = pinyin.TokenList([dictionaryonline.gTrans(expression, self.config.dictlanguage)])
    
            # DEBUG: Nick wants to do something with audio for measure words here?
            # " [sound:MW]" # DEBUG - pass to audio loop
    
        # Do the updates on the fields the user has requested:
        updaters = {
                'reading' : (True,                                     lambda: self.generatereading(dictreading)),
                'meaning' : (self.config.meaninggeneration,            lambda: self.generatemeanings(dictmeanings)),
                'mw'      : (self.config.detectmeasurewords,           lambda: self.generatemeasureword(dictmeasurewords)),
                'audio'   : (self.config.audiogeneration,              lambda: self.generateaudio(notifier, dictreading)),
                'color'   : (self.config.colorizedcharactergeneration, lambda: self.generatecoloredcharacters(expression))
            }
    
        for key, (enabled, updater) in updaters.items():
            # Skip updating if no suitable field, we are disabled, or the field has text
            fieldName = fieldNames[key]
            if fieldName == None or not(enabled) or fact[fieldName].strip() != u"":
                continue
        
            # Update the value in that field
            value = updater()
            if value != None and value != fact[fieldName]:
                fact[fieldName] = value