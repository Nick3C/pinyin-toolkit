# -*- coding: utf-8 -*-

import os

import config
from db import database
import dictionary
import dictionaryonline
import factproxy
import media
import meanings
import numbers
import model
import transformations
import updatergraph
import utils
import random
import re

from logger import log


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
    def __init__(self, notifier, mediamanager, config):
        self.graphbasedupdater = updatergraph.GraphBasedUpdater(notifier, mediamanager, config)
    
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
        
        # Use the new framework to fill out the fact for now:
        known, needed = partitionfact(fact, expression=expression)
        unpreservedneeded = filter(shouldupdatefield(self.graphbasedupdater.config), needed)
        for key, value in self.graphbasedupdater.fillneeded(utils.updated(known, { "mwfieldinfact" : "mw" in fact }), unpreservedneeded).items(): # HACK ALERT: can't think of a nicer way to do mwfieldinfact
            fact[key] = factproxy.markgeneratedfield(value)

def shouldupdatefield(theconfig):
    return lambda field: config.updatecontrolflags[field] is None or theconfig.settings[config.updatecontrolflags[field]]

def partitionfact(fact, **extraknowns):
    known, needed = {}, set()
    for field, value in utils.updated(dict([(key, fact[key]) for key in fact]), extraknowns).items():
        if factproxy.isgeneratedfield(field, value):
            needed.add(field)
        else:
            known[field] = value

    return (known, needed)
