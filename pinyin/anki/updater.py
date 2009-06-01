from pinyin import pinyin, transformations, dictionary, dictionaryonline, media

import utils

class MeaningFormatter(object):
    def __init__(self, config):
        self.config = config
    
    def splitmeanings(self, dictmeanings):
        # If we didn't get any information from the dictionary, just give up
        if dictmeanings == None:
            return None, None
        
        # Replace all occurence of CL: with MW: as that is more meaningful
        dictmeanings = [dictmeaning.replace("CL:", "MW:") for dictmeaning in dictmeanings]
        
        if not(self.config.detectmeasurewords):
            # Return any measure words as part of the list of meanings
            onlymeanings, measurewords = dictmeanings, None
        else:
            # OK, we're looking for measure words - scan each meaning looking for some
            onlymeanings, measurewords = [], []
            for dictmeaning in dictmeanings:
                measureword = self.parsemeasureword(dictmeaning)
                if measureword != None:
                    # It's a measure word - append to measure word list
                    measurewords.append(measureword)
                else:
                    # Not a measure word, so it must be a plain meaning
                    onlymeanings.append(dictmeaning)
        
        return onlymeanings, measurewords
    
    # Allows us to detect measure word data from dictionary
    # Currently only English CC-CEDICT support this function
    def parsemeasureword(self, meaning):
        # TODO: this routine is somewhat broken
        if meaning.startswith("MW:"):
            # use a for loop to go through each reading entry to collect any starting with "CL:", cut into an array
            # go through the array here with each of the MW lines
            # DEBUG - need a fix for some CC-CEDICT lines that are formatted "CL:[char1],[char2],[char3]" but this is not common and not very important

            # chose either simplified or traditional measure word based on preferences
            # somewhat complex format of this statement allows for easy inclusion of other dictionaries in the future
            MWposdiv = meaning.find("|")
            if self.config.dictlanguage == "en":
                if self.config.prefersimptrad == "simp":
                    MWposstart = MWposdiv - 1
                else:
                    MWposstart = MWposdiv + 1
                MWposend=MWposstart+1
                MWentry = meaning[MWposstart:MWposend] + meaning[MWposdiv+2:] # cut measure word as per selection and add to pinyin         
            else:
                MWentry = meaning
            mwaduio = " [sound:MW]" # DEBUG - pass to audio loop
            MWentry = MWentry.replace("["," - ").replace("]","") + mwaduio
        
            return MWentry
        else:
            return None

class FieldUpdater(object):
    def __init__(self, config, dictionary, availablemedia, notifier):
        self.config = config
        self.dictionary = dictionary
        self.availablemedia = availablemedia
        self.notifier = notifier
    
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
                onlymeanings, measurewords = MeaningFormatter(self.config).splitmeanings(dictmeanings)
    
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