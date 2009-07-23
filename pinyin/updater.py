#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import config
import dictionary
import dictionaryonline
import media
import meanings
import numbers
import model
import transformations
import utils
import re

from logger import log

import random

def preparetokens(config, tokens):
    if config.colorizedpinyingeneration:
        tokens = transformations.colorize(config.tonecolors, tokens)

    return model.flatten(tokens, tonify=config.shouldtonify)

def generateaudio(notifier, mediamanager, config, dictreading):
    mediapacks = mediamanager.discovermediapacks()
    if len(mediapacks) == 0:
        # Show a warning the first time we detect that we're missing a sound pack
        notifier.infoOnce("The Pinyin Toolkit cannot find an audio pack for text-to-speech.  We reccomend you either disable the audio functionality "
                          + "or install the free Chinese-Lessons.com Mandarin Sounds audio pack using the Audio tab in Settings > Pinyin Toolkit Preferences.")
        
        # There is no way we can generate an audio reading with no packs - give up
        return None
    
    # Get the best media pack to generate the audio, along with the string of files from that pack we need to take
    mediapack, output, _mediamissing = transformations.PinyinAudioReadings(mediapacks, config.audioextensions).audioreading(dictreading)
    
    # Construct the string of audio tags from the optimal choice of sounds
    output_tags = u""
    for outputfile in output:
        # Install required media in the deck as we go, getting the canonical string to insert into the sound field upon installation
        output_tags += "[sound:%s]" % mediamanager.importtocurrentdeck(os.path.join(mediapack.packpath, outputfile))
    
    return output_tags

class FieldUpdaterFromAudio(object):
    def __init__(self, notifier, mediamanager, config):
        self.notifier = notifier
        self.mediamanager = mediamanager
        self.config = config
    
    def reformataudio(self, audio):
        output = u""
        for recognised, match in utils.regexparse(re.compile(ur"\[sound:([^\]]*)\]"), audio):
            if recognised:
                # Must be a sound tag - leave it well alone
                output += match.group(0)
            else:
                # Process as if this non-sound tag were a reading, in order to turn it into some tags
                output += generateaudio(self.notifier, self.mediamanager, self.config, [model.Word(*model.tokenize(match))])
        
        return output
    
    def updatefact(self, fact, audio):
        # Don't bother if the appropriate configuration option is off or update will fail
        if not(self.config.forcepinyininaudiotosoundtags) or 'audio' not in fact:
            return
        
        # Identify probable pinyin in the user's freeform input, look up audio for it, and replace
        fact['audio'] = self.reformataudio(audio)

class FieldUpdaterFromMeaning(object):
    def __init__(self, config):
        self.config = config
    
    def reformatmeaning(self, meaning):
        output = u""
        for recognised, match in utils.regexparse(re.compile(ur"\(([0-9]+)\)"), meaning):
            if recognised:
                # Should reformat the number
                output += self.config.meaningnumber(int(match.group(1)))
            else:
                # Output is just unicode, append it directly
                output += match
        
        return output
    
    def updatefact(self, fact, meaning):
        # Don't bother if the appropriate configuration option is off or update will fail
        if not(self.config.forcemeaningnumberstobeformatted) or 'meaning' not in fact:
            return

        # Simply replace any occurences of (n) with the string self.config.meaningnumber(n)
        fact['meaning'] = self.reformatmeaning(meaning)

class FieldUpdaterFromReading(object):
    def __init__(self, config):
        self.config = config
    
    def updatefact(self, fact, reading):
        # Don't bother if the appropriate configuration option is off
        if not(self.config.forcereadingtobeformatted):
            return
        
        # Use the unprotected update method to do the bulk of the work.
        # The unprotected version is used for the mass filler.
        self.updatefactalways(fact, reading)
    
    def updatefactalways(self, fact, reading):
        # We better still give it a miss if the update will fail
        if 'reading' not in fact:
            return
    
        # Identify probable pinyin in the user's freeform input, reformat them according to the
        # current rules, and pop the result back into the field
        fact['reading'] = preparetokens(self.config, [model.Word(*model.tokenize(reading))])

class FieldUpdaterFromExpression(object):
    def __init__(self, notifier, mediamanager, config, database):
        self.notifier = notifier
        self.mediamanager = mediamanager
        self.config = config
        self.dictionaries = dictionary.PinyinDictionary.loadall(database)
    
    dictionary = property(lambda self: self.dictionaries(self.config.dictlanguage))
    
    #
    # Generation of field contents
    #
    
    def generatereading(self, dictreading):
        # Put pinyin into lowercase before anything else is done to it
        # TODO: do we really want lower case here? If so, we should do it for colorized pinyin as well.
        return preparetokens(self.config, dictreading).lower()
    
    def generateaudio(self, dictreading):
        return generateaudio(self.notifier, self.mediamanager, self.config, dictreading)
    
    def generatemeanings(self, expression, dictmeanings):
        if dictmeanings == None:
            # We didn't get any meanings, don't update the field
            return None
        
        # Consider sandhi in meanings - you never know, there might be some!
        dictmeanings = [transformations.tonesandhi(dictmeaning) for dictmeaning in dictmeanings]
        
        if self.config.hanzimasking:
            # Hanzi masking is on: scan through the meanings and remove the expression itself
            dictmeanings = [transformations.maskhanzi(expression, self.config.formathanzimaskingcharacter(), dictmeaning) for dictmeaning in dictmeanings]

        # Prepare all the meanings by flattening them and removing empty entries
        meanings = [meaning for meaning in [preparetokens(self.config, dictmeaning) for dictmeaning in dictmeanings] if meaning.strip != '']
        
        # Scan through the meanings and replace instances of 'surname Foo' with a masked version
        lookslikesurname = lambda what: what.lower().startswith("surname ") and " " not in what[len("surname ")]
        meanings = [lookslikesurname(meaning) and "(a surname)" or meaning for meaning in meanings]
        
        if len(meanings) == 0:
            # After flattening and stripping, we didn't get any meanings: don't update the field
            return None
        
        # Use the configuration to insert numbering etc
        return self.config.formatmeanings(meanings)
    
    def generatemeasureword(self, dictmeasurewords):
        if dictmeasurewords == None or len(dictmeasurewords) == 0:
            # No measure word, so don't update the field
            return None
        
        # Concatenate the measure words together with - before we put them into the MW field
        return preparetokens(self.config, dictionary.flattenmeasurewords(dictmeasurewords))
    
    def generatemwaudio(self, noundictreading, dictmeasurewords):
        if dictmeasurewords == None or len(dictmeasurewords) == 0:
            # No measure word, so don't update the field
            return None
    
        dictreading = []
        for _, mwpinyinwords in dictmeasurewords:
            # The audio field will contain <random number> <mw> <noun> for every possible MW
            # NB: we explicitly encode the tokens rather than doing a lookup because e.g. 几 has
            # several readings, but we know precisely the one we want here and can avoid ambiguity
            dictreading.append(model.Word(random.choice(numbers.hanziquantitypinyin)))
            dictreading.extend(mwpinyinwords)
            dictreading.extend(noundictreading)
            # This comma doesn't currently do anything, but it might come in useful if we
            # add delay generation in the audio code later on
            dictreading.append(model.Word(model.Text(", ")))
        
        # Only apply the sandhi generator at this point: we have carefully avoided doing it for the
        # input up to now (especially for the noundictreading). Probably doesn't make a difference
        # with the current implementation, but better safe than sorry.
        return generateaudio(self.notifier, self.mediamanager, self.config, transformations.tonesandhi(dictreading))
    
    def generatecoloredcharacters(self, expression):
        return model.flatten(transformations.colorize(self.config.tonecolors, transformations.tonesandhi(self.dictionary.tonedchars(expression))))

    # Future support will need to be dictionary-based and will require a lot more work
    # Will need to be a bit complex:
    # Stage 1 - match exact words from dict
    # Stage 2 - mix-and-match:
                # find longest word in phrase
                # find next longest word in remaining parts
                # recursive
    # Stage 3 - fall back on gTrans for unknown characters [mark orange, different from tone2] 
    # Stage 4 - return unfound characters [mark dark red]

    # be wary of returning wrong characters one-to-many conversions(especially a problem with single-char words)
    # return single character words in a lighter grey (to indicate they need checking)
    # Must not return prompt (otherwise well-configured decks will auto-generate unwatned traditional cards)
    def generateincharactersystem(self, expression, charmode):
        log.info("Doing conversion of %s into %s characters", expression, charmode)

        # Query Google for the conversion, returned in the format: ["社會",[["noun","社會","社會","社會"]]]
        if charmode=="simp":
            glangcode="zh-CN"
        else:
            glangcode="zh-TW"
        meanings = dictionaryonline.gTrans(expression, glangcode, False)
        
        if meanings == None or len(meanings) == 0:
            # No conversion, so give up and return the input expression
            return expression
        else:
            # Conversion is stored in the first 'meaning'
            return model.flatten(meanings[0])
    
    def weblinkgeneration(self, expression):
        # Generate a list of links to online dictionaries, etc to query the expression
        return " ".join(['[<a href="' + urltemplate.replace("{searchTerms}", utils.urlescape(expression)) + '" title="' + tooltip + '">' + text + '</a>]' for text, tooltip, urltemplate in self.config.weblinks])

    #
    # Core updater routines
    #
    
    def getdictreading(self, expression):
        dictreadingsources = [
                # Get the reading by considering the text as a (Western) number
                lambda: numbers.readingfromnumberlike(expression, self.dictionary),
                # Use CEDICT to get reading (always succeeds)
                lambda: self.dictionary.reading(expression)
            ]
        
        # Find the first source that returns a sensible reading
        for lookup in dictreadingsources:
            dictreading = lookup()
            if dictreading != None:
                return dictreading
  
        raise AssertionError("The CEDICT reading lookup should always succeed, but it failed on %s" % expression)
    
    def updatefact(self, fact, expression):
        # AutoBlanking Feature - If there is no expression, zeros relevant fields
        # DEBUG - add feature to store the text when a lookup is performed. When new text is entered then allow auto-blank any field that has not been edited
        if expression == None or expression.strip() == u"":
            for key in ["reading", "meaning", "color", "trad", "simp", "weblinks"]:
                if key in fact:
                    fact[key] = u""
            
            # DEBUG Me - Auto generated pinyin should be at least "[sound:" + ".xxx]" (12 characters) plus pinyin (max 6). i.e. 18
            # DEBUG - Split string around "][" to get the audio of each sound in an array. Blank the field unless any one string is longer than 20 characters
            # Exploit the fact that pinyin text-to-speech pinyin should be no longer than 18 characters to guess that anything longer is user generated
            # MaxB comment: I don't think that will work, because we import the Chinese-Lessons.com Mandarin Sounds into anki and it gives them /long/ names.
            # Instead, how about we check if all of the audio files referenced are files in the format pinyin<tone>.mp3?
            if 'audio' in fact and len(fact['audio']) < 40:
                fact['audio'] = u""
            
            # For now this is a compromise in safety and function.
            # longest MW should be: "? - zhangì (9 char)
            # shortest possible is "? - ge" 6 char so we will autoblank if less than 12 letters
            # this means blanking will occur if one measure word is there but not if two (so if user added any they are safe)
            if 'mw' in fact and len(fact['mw']) < 12: 
                fact['mw'] = u""
            
            # TODO: Nick added this to give up after auto-blanking. He claims it removes a minor
            # delay, but I'm not sure where the delay originates from, which worries me:
            return
        
        # Apply tone sandhi: this information is needed both by the sound generation
        # and the colorisation, so we can't do it in generatereading
        dictreading = self.getdictreading(expression)
        dictreadingsandhi = transformations.tonesandhi(dictreading)
  
        # Preload the meaning, but only if we absolutely must
        if self.config.needmeanings:
            dictmeaningssources = [
                    # Use CEDICT to get meanings
                    (None,
                     lambda: self.dictionary.meanings(expression, self.config.prefersimptrad)),
                    # Interpret Hanzi as numbers. NB: only consult after CEDICT so that we
                    # handle curious numbers such as 'liang' using the dictionary
                    (None,
                     lambda: (numbers.meaningfromnumberlike(expression, self.dictionary), None))
                ] + (self.config.shouldusegoogletranslate and [
                    # If the dictionary can't answer our question, ask Google Translate.
                    # If there is a long word followed by another word then this will be treated as a phrase.
                    # Phrases are also queried using googletranslate rather than the local dictionary.
                    # This helps deal with small dictionaries (for example French)
                    ('<br /><span style="color:gray"><small>[Google Translate]</small></span><span> </span>',
                     lambda: (dictionaryonline.gTrans(expression, self.config.dictlanguage), None))
                ] or [])
            
            # Find the first source that returns a sensible meaning
            for dictmeaningssource, lookup in dictmeaningssources:
                dictmeanings, dictmeasurewords = lookup()
                if dictmeanings != None or dictmeasurewords != None:
                    break
            
            # If the user wants the measure words to be folded into the definition or there
            # is no MW field for us to split them out into, fold them in there
            if not(self.config.detectmeasurewords) or "mw" not in fact:
                # NB: do NOT overwrite the old dictmeasurewords, because we still want to use the
                # measure words for e.g. measure word audio generation
                dictmeanings = dictionary.combinemeaningsmws(dictmeanings, dictmeasurewords)
            
            # NB: expression only used for Hanzi masking here
            meaning = self.generatemeanings(expression, dictmeanings)
            if meaning and dictmeaningssource:
                # Append attribution to the meaning if we have any
                meaning = meaning + dictmeaningssource

        # Generate translations of the expression into simplified/traditional on-demand
        expressionviews = utils.FactoryDict(lambda simptrad: self.generateincharactersystem(expression, simptrad))
        
        # Update the expression is option is turned on and the preference simp/trad is different to expression (i.e. needs correcting)
        expressionupdated = False
        if self.config.forceexpressiontobesimptrad and (expression != expressionviews[self.config.prefersimptrad]):
            expression = expressionviews[self.config.prefersimptrad]
            expressionupdated = True

        # Do the updates on the fields the user has requested:
        # NB: when adding an updater to this list, make sure that you have
        # added it to the updatecontrolflags dictionary in Config as well!
        updaters = {
                'expression' : lambda: expression,
                'reading'    : lambda: self.generatereading(dictreadingsandhi),
                'meaning'    : lambda: meaning,
                'mw'         : lambda: self.generatemeasureword(self.config.detectmeasurewords and dictmeasurewords or None),
                'audio'      : lambda: self.generateaudio(dictreadingsandhi),
                'mwaudio'    : lambda: self.generatemwaudio(dictreading, dictmeasurewords),
                'color'      : lambda: self.generatecoloredcharacters(expression),
                'trad'       : lambda: (expressionviews["trad"] != expressionviews["simp"]) and expressionviews["trad"] or None,
                'simp'       : lambda: (expressionviews["trad"] != expressionviews["simp"]) and expressionviews["simp"] or None,
                'weblinks'   : lambda: self.weblinkgeneration(expression)
            }

        # Loop through each field, deciding whether to update it or not
        for key, updater in updaters.items():
            # A hint for reading this method: read the stuff inside the if not(...):
            # as an assertion that has to be valid before we can proceed with the update.
            
            # If this option has been disabled or the field isn't present then jump to the next update.
            # Expression is always updated because some parts of the code call updatefact with an expression
            # that is not yet set on the fact, and we need to make sure that it arrives. This is OK, because
            # we only actually modify a directly user-entered expression when forceexpressiontobesimptrad is on.
            #
            # NB: please do NOT do this if key isn't in updatecontrolflags, because that
            # indicates an error with the Toolkit that I'd like to get an exception for!
            if not(key in fact and (key == "expression" or config.updatecontrolflags[key] is None or self.config.settings[config.updatecontrolflags[key]])):
                continue
            
            # If the field is not empty already then skip (so we don't overwrite it), unless:
            # a) this is the expression field, which should always be over-written with simp/trad
            # b) this is the weblinks field, which must always be up to date
            # c) this is the color field and we have just forced the expression to change,
            #    in which case we'd like to overwrite the colored characters regardless
            if not(fact[key].strip() == u"" or key in ["expression", "weblinks"] or (key == "color" and expressionupdated)):
                continue
            
            # Fill the field with the new value, but only if we have one and it is necessary to do so
            value = updater()
            if value != None and value != fact[key]:
                fact[key] = value
