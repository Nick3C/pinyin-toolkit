# -*- coding: utf-8 -*-

import os

import config
from db import database
import dictionary
import dictionaryonline
import media
import meanings
import numbers
import model
import transformations
from utils import * # NB: we get "all" from here on Python 2.4
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

class Reformatter(object):
    def __init__(self, notifier, mediamanager, config):
        self.notifier = notifier
        self.mediamanager = mediamanager
        self.config = config
        self.reformatters = [
                ("audio", lambda: self.config.forcepinyininaudiotosoundtags, self.reformataudio, []),
                ("meaning", lambda: self.config.forcemeaningnumberstobeformatted, self.reformatmeaning, []),
                ("reading" , lambda: self.config.forcereadingtobeformatted, self.reformatreading, []),
                ("expression", lambda: self.config.forceexpressiontobesimptrad, self.reformatexpression, ["simptrad"])
            ]
    
    def reformataudio(self, audio):
        output = u""
        for recognised, match in regexparse(re.compile(ur"\[sound:([^\]]*)\]"), audio):
            if recognised:
                # Must be a sound tag - leave it well alone
                output += match.group(0)
            else:
                # Process as if this non-sound tag were a reading, in order to turn it into some tags
                output += generateaudio(self.notifier, self.mediamanager, self.config, [model.Word(*model.tokenize(match))])

        return output

    def reformatmeaning(self, meaning):
        output = u""
        for recognised, match in regexparse(re.compile(ur"\(([0-9]+)\)"), meaning):
            if recognised:
                # Should reformat the number
                output += self.config.meaningnumber(int(match.group(1)))
            else:
                # Output is just unicode, append it directly
                output += match

        return output

    def reformatreading(self, reading):
        return preparetokens(self.config, [model.Word(*model.tokenize(reading))])

    def reformatexpression(self, expression, simptrad):
        return simptrad[self.config.prefersimptrad] or expression

    def reformatfield(self, field, graph):
        for reformatwhat, shouldreformat, reformatter, reformatusings in self.reformatters:
            if reformatwhat != field:
                continue
        
            if all([(it in graph) and (graph[it]() is not None) for it in [reformatwhat] + reformatusings]) and shouldreformat():
                return reformatter(graph[field](), *[graph[reformatusing]() for reformatusing in reformatusings])
        
        return graph[field]()

class GraphBasedUpdater(object):
    def __init__(self, notifier, mediamanager, config):
        self.notifier = notifier
        self.mediamanager = mediamanager
        self.config = config
        self.dictionaries = dictionary.PinyinDictionary.loadall()
        
        self.updaters = [
                ("simptrad", self.expression2simptrad, ["expression"]),
                ("trad", lambda x: x["simp"] != x["trad"] and x["trad"] or "", ["simptrad"]),
                ("simp", lambda x: x["simp"] != x["trad"] and x["simp"] or "", ["simptrad"]),
                ("expression", lambda x: x, ["simp"]),
                ("expression", lambda x: x, ["trad"]),
        
                ("dictmeaningsmwssource", self.expression2dictmeaningsmwssource, ["expression"]),
                ("dictmeaningsmws", lambda x: x[0], ["dictmeaningsmwssource"]),
                ("dictmeaningssource", lambda x: x[1], ["dictmeaningsmwssource"]),
                ("mergeddictmeaningsmws", self.dictmeaningsmws2mergeddictmeaningsmws, ["dictmeaningsmws", "mwfieldinfact"]),
                ("mergeddictmeanings", lambda x: x[0], ["mergeddictmeaningsmws"]),
                ("mergeddictmws", lambda x: x[1], ["mergeddictmeaningsmws"]),
                ("meaning", self.dictmeaningsmws2meaning, ["expression", "mergeddictmeanings", "dictmeaningssource"]), # Need expression for Hanzi masking
        
                ("mergeddictmeaningsmws", self.meaning2mergeddictmeaningsmws, ["meaning"]),
        
                ("dictmws", lambda x: x[1], ["dictmeaningsmws"]),
                ("dictmws", self.mw2dictmws, ["mw"]), # TODO: think carefully about this and mergeddictmws for the update story here
                ("mw", self.mergeddictmws2mw, ["mergeddictmws"]),
                ("mwaudio", self.mergeddictmwdictreading2mwaudio, ["dictmws", "dictreading"]), # Need dictreading for the noun
        
                ("dictreading", self.expression2dictreading, ["expression"]),
                ("reading", self.dictreading2reading, ["dictreading"]),
                ("dictreading", self.reading2dictreading, ["reading"]),
                ("color", self.expressiondictreading2color, ["expression", "dictreading"]),
                ("audio", self.dictreading2audio, ["dictreading"]),
                
                ("weblinks", self.expression2weblinks, ["expression"])
            ]

    updateablefields = property(lambda self: set([field for field, _, _ in self.updaters]))
    dictionary = property(lambda self: self.dictionaries(self.config.dictlanguage))

    def expression2simptrad(self, expression):
        result = {}
        for charmode, glangcode in [("simp", "zh-CN"), ("trad", "zh-TW")]:
            # Query Google for the conversion, returned in the format: ["社會",[["noun","社會","社會","社會"]]]
            log.info("Doing conversion of %s into %s characters", expression, charmode)
            meanings = dictionaryonline.gTrans(expression, glangcode, False)

            if meanings is None or len(meanings) == 0:
                # No conversion, so give up and return the input expression
                result[charmode] = expression
            else:
                # Conversion is stored in the first 'meaning'
                result[charmode] = model.flatten(meanings[0])
        
        return result

    def expression2dictmeaningsmwssource(self, expression):
        dictmeaningssources = [
                # Use CEDICT to get meanings
                ("",
                 lambda: self.dictionary.meanings(expression, self.config.prefersimptrad)),
                # Interpret Hanzi as numbers. NB: only consult after CEDICT so that we
                # handle curious numbers such as 'liang' using the dictionary
                ("",
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
            dictmeanings, dictmws = lookup()
            if dictmeanings != None or dictmws != None:
                return (dictmeanings or [], dictmws or []), dictmeaningssource
        
        # No information available
        return None

    def dictmeaningsmws2mergeddictmeaningsmws(self, dictmeaningsmws, mwfieldinfact):
        dictmeanings, dictmws = dictmeaningsmws
        
        # If the user wants the measure words to be folded into the definition or there
        # is no MW field for us to split them out into, fold them in there
        if not(self.config.detectmeasurewords) or not mwfieldinfact:
            return dictionary.combinemeaningsmws(dictmeanings, dictmws), []
        else:
            return dictmeanings, dictmws

    def dictmeaningsmws2meaning(self, expression, dictmeanings, dictmeaningssource):
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
        return self.config.formatmeanings(meanings) + dictmeaningssource

    def meaning2mergeddictmeaningsmws(self, meaning):
        # TODO
        raise NotImplementedError("meaning2mergeddictmeaningsmws: need parser")

    def mergeddictmws2mw(self, mergeddictmws):
        # Concatenate the measure words together with - before we put them into the MW field
        return preparetokens(self.config, dictionary.flattenmeasurewords(mergeddictmws))

    def mw2dictmws(self, mw):
        # TODO
        return NotImplementedError("mw2mergeddictmws: need parser")

    def mergeddictmwdictreading2mwaudio(self, mergeddictmws, noundictreading):
        dictreading = []
        for _, mwpinyinwords in mergeddictmws:
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

    def expression2dictreading(self, expression):
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
                return transformations.tonesandhi(dictreading)
  
        raise AssertionError("The CEDICT reading lookup should always succeed, but it failed on %s" % expression)

    def dictreading2reading(self, dictreading):
        # Put pinyin into lowercase before anything else is done to it
        # TODO: do we really want lower case here? If so, we should do it for colorized pinyin as well.
        return preparetokens(self.config, model.formatreadingfordisplay(dictreading)).lower()

    def reading2dictreading(self, reading):
        return [model.Word(*model.tokenize(reading))]

    def expressiondictreading2color(self, expression, dictreading):
        return model.flatten(transformations.colorize(self.config.tonecolors, model.tonedcharactersfromreading(expression, dictreading)))

    def dictreading2audio(self, dictreading):
        return generateaudio(self.notifier, self.mediamanager, self.config, dictreading)

    def expression2weblinks(self, expression):
        # Generate a list of links to online dictionaries, etc to query the expression
        return " ".join(['[<a href="' + urltemplate.replace("{searchTerms}", urlescape(expression)) + '" title="' + tooltip + '">' + text + '</a>]' for text, tooltip, urltemplate in self.config.weblinks])


    def fill(self, graph, field):
        # Bbetter try and compute the field contents from dependent fields.
        # NB: there may be more than one way to fill out a field. We take the view
        # that any valid way to fill out a field is acceptable, and don't try
        # and prioritise any particular path right now.
        for updatewhat, updatefunction, updateusings in self.updaters:
            if updatewhat != field:
                continue
    
            # Satisfy dependencies of the update function recursively (via the thunks in the graph)
            if all([(updateusing in graph) and (graph[updateusing]() is not None) for updateusing in updateusings]):
                value = updatefunction(*[graph[updateusing]() for updateusing in updateusings])
                if value is not None:
                    return value

        # All else failed. We're just going to have to give up!
        return None

    def filledgraph(self, known):
        graph = {}
        
        # Fill with known facts to begin with - wrap in thunks so that we know everything in
        # the graph is certainly a thunk
        for field in known:
            graph[field] = Thunk(lambda field=field: known[field])
        
        # Fill all things we know how to reach which are not known facts with that computation
        for field in self.updateablefields:
            if field not in known:
                graph[field] = Thunk(lambda field=field: self.fill(graph, field))
        
        return graph