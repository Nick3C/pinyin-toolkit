#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from pinyin import dictionary, dictionaryonline, media, meanings, pinyin, transformations
from pinyin.logger import log


class FieldUpdater(object):
    def __init__(self, mw, notifier, config, dictionary):
        self.mw = mw
        self.notifier = notifier
        self.config = config
        self.dictionary = dictionary
    
    def preparetokens(self, tokens):
        if self.config.colorizedpinyingeneration:
            tokens = transformations.Colorizer(self.config.tonecolors).colorize(tokens)
    
        return tokens.flatten(tonify=self.config.shouldtonify)
    
    #
    # Media discovery
    #
    
    def discoverlegacymedia(self):
        # NB: we used to do this when initialising the toolkit, but that dosen't work,
        # for the simple reason that if you change deck the media should change, but
        # we can't hook that event
        
        # I can ask Damien for a hook if you like. He has been very good with these sort of things in the past.
        
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
        
        # Use the configuration to insert numbering etc
        return self.config.formatmeanings(meanings)
    
    def generatemeasureword(self, dictmeasurewords):
        if dictmeasurewords == None or len(dictmeasurewords) == 0:
            # No measure word, so don't update the field
            return None
        
        # Just use the first measure word meaning, if there was more than one
        return self.preparetokens(dictmeasurewords[0])
    
    def generatecoloredcharacters(self, expression):
        return transformations.Colorizer(self.config.tonecolors).colorize(self.dictionary.tonedchars(expression)).flatten()
    
    #
    # Core updater routine
    #
    
    def updatefact(self, notifier, fact, expression):
        # AutoBlanking Feature - If there is no expression, zeros relevant fields
        # DEBUG - add feature to store the text when a lookup is performed. When new text is entered then allow auto-blank any field that has not been edited
        if 'expression' in fact and not(fact['expression']):
            for key in ["reading", "meaning", "color"]:
                if key in fact:
                    fact[key] = u""
            
            # DEBUG Me - Auto generated pinyin should be at least "[sound:" + ".xxx]" (12 characters) plus pinyin (max 6). i.e. 18
            # DEBUG - Split string around "][" to get the audio of each sound in an array. Blank the field unless any one string is longer than 20 characters
            # Exploit the fact that pinyin text-to-speech pinyin should be no longer than 18 characters to guess that anything longer is user generated
            # MaxB comment: I don't think that will work, because we import the Mandarin Sounds into anki and it gives them /long/ names.  Instead, how
            # about we check if all of the audio files referenced are files in the format pinyin<tone>.mp3?
            if 'audio' in fact and len(fact['audio']) < 40:
                fact['audio'] = u""
            
            # For now this is a compromise in safety and function.
            # longest MW should be: "? - zhang“ (9 char)
            # shortest possible is "? - ge" 6 char so we will autoblank if less than 12 letters
            # this means blanking will occur if one measure word is there but not if two (so if user added any they are safe)
            if 'mw' in fact and len(fact['mw']) < 12: 
                fact['mw'] = u""
    
        # Figure out the reading for the expression field
        dictreading = self.dictionary.reading(expression)
    
        # Preload the meaning, but only if we absolutely have to
        if self.config.needmeanings:
            if self.config.detectmeasurewords and "mw" in fact:
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
            if not(key in fact) or not(enabled) or fact[key].strip() != u"":
                continue
        
            # Update the value in that field
            value = updater()
            if value != None and value != fact[key]:
                fact[key] = value