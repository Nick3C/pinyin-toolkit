#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pinyin import pinyin, transformations, dictionary, dictionaryonline, media, meanings

import utils

class FieldUpdater(object):
    def __init__(self, config, dictionary, availablemedia, notifier):
        self.config = config
        self.dictionary = dictionary
        self.availablemedia = availablemedia
        self.notifier = notifier
        
        self.meaningformatter = meanings.MeaningFormatter(self.config.detectmeasurewords,
                                                          self.dictionary.simplifiedcharindex,
                                                          self.config.prefersimptrad)
    
    #
    # Generation
    #
    
    def generatereading(self, reading):
        if self.config.colorizedpinyingeneration:
            reading = transformations.Colorizer().colorize(reading)
    
        # TODO: do we really want lower case here? If so, we should do it for colorized pinyin as well.
        return reading.flatten(tonify=self.config.tonify).lower() # Put pinyin into lowercase before anything is done to it
    
    def generateaudio(self, notifier, reading):
        output, mediamissing = transformations.PinyinAudioReadings(self.availablemedia, self.config.audioextensions).audioreading(reading)
    
        # Show a warning the first time we detect that we're missing some sounds
        if mediamissing:
            notifier.infoOnce("We appear to be missing some audio samples. This might be our fault, but if you haven't already done so, "
                              + "please use 'Tools' -> 'Download Mandarin text-to-speech Audio Files' to install the samples. Alternatively, "
                              + "you can disable the text-to-speech functionality in the Pinyin Toolkit settings.")
    
        return output
    
    def generatemeanings(self, meanings):
        if meanings == None or len(meanings) == 0:
            # We didn't get any meanings, don't update the field
            return None
        
        # Don't add meanings if it is disabled or there is only one meaning
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
    
    def generatemeasureword(self, measurewords):
        if measurewords == None or len(measurewords) == 0:
            # No measure word, so don't update the field
            return None
        
        # Just use the first measure word meaning, if there was more than one
        return measurewords[0]
    
    def generatecoloredcharacters(self, expression):
        return transformations.Colorizer().colorize(self.dictionary.tonedchars(expression)).flatten()
    
    #
    # Core updater routine
    #
    
    def updatefact(self, notifier, fact, expression):
        # Discover the final field names
        fieldNames = dict([(key, utils.chooseField(candidateFieldNames, fact)) for key, candidateFieldNames in self.config.candidateFieldNamesByKey.items()])
    
        # If there is no expression, zero every field
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
        reading = self.dictionary.reading(expression)
    
        # Preload the meaning, but only if we absolutely have to
        if utils.needmeanings(self.config):
            dictmeanings = self.dictionary.meanings(expression)
            
            # If the dictionary can't answer our question, ask Google Translate
            # If there is a long word followed by another word then this will be treated as a phrase
            # Phrases are also queried using googletranslate rather than the local dictionary
            # This helps deal with small dictionaries (for example French)
            if dictmeanings == None and self.config.fallbackongoogletranslate:
                onlymeanings = dictionaryonline.gTrans(expression, self.config.dictlanguage)
                measurewords = None
            else:
                onlymeanings, measurewords = self.meaningformatter.splitmeanings(dictmeanings)
    
        # Do the updates on the fields the user has requested:
        updaters = {
                'reading' : (True,                                     lambda: self.generatereading(reading)),
                'meaning' : (self.config.meaninggeneration,            lambda: self.generatemeanings(onlymeanings)),
                'mw'      : (self.config.detectmeasurewords,           lambda: self.generatemeasureword(measurewords)),
                'audio'   : (self.config.audiogeneration,              lambda: self.generateaudio(notifier, reading)),
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