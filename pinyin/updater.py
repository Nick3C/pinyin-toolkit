#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import config
import dictionary
import dictionaryonline
import media
import meanings
import numbers
import pinyin
import transformations
import utils
import re

from logger import log

import random

def preparetokens(config, tokens):
    if config.colorizedpinyingeneration:
        tokens = transformations.colorize(config.tonecolors, tokens)

    return pinyin.flatten(tokens, tonify=config.shouldtonify)

def generateaudio(notifier, mediamanager, config, dictreading):
    mediapacks = mediamanager.discovermediapacks()
    if len(mediapacks) == 0:
        # Show a warning the first time we detect that we're missing a sound pack
        notifier.infoOnce("The Pinyin Toolkit cannot find an audio pack for text-to-speech.  We reccomend you either disable the audio functionality "
                          + "or install the free Chinese-Lessons.com Mandarin Sounds audio pack using the Audio tab in Tool > Preferences.")
        
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
                output += generateaudio(self.notifier, self.mediamanager, self.config, [pinyin.Word(*pinyin.tokenize(match))])
        
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
        fact['reading'] = preparetokens(self.config, [pinyin.Word(*pinyin.tokenize(reading))])

class FieldUpdaterFromExpression(object):
    def __init__(self, notifier, mediamanager, config):
        self.notifier = notifier
        self.mediamanager = mediamanager
        self.config = config
    
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
        
        # Scan through the meanings and replace instances of 'surname: Foo' with a masked version
        lookslikesurname = lambda what: what.lower().startswith("surname") and " " not in what[len("surname ")]
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
            dictreading.extend(self.getdictreading(random.choice(numbers.hanziquantitywords)))
            dictreading.extend(mwpinyinwords)
            dictreading.extend(noundictreading)
            # This comma doesn't currently do anything, but it might come in useful if we
            # add delay generation in the audio code later on
            dictreading.append(pinyin.Word(pinyin.Text(", ")))
        
        # Only apply the sandhi generator at this point: we have carefully avoided doing it for the
        # input up to now (especially for the noundictreading). Probably doesn't make a difference
        # with the current implementation, but better safe than sorry.
        return generateaudio(self.notifier, self.mediamanager, self.config, transformations.tonesandhi(dictreading))
    
    def generatecoloredcharacters(self, expression):
        return pinyin.flatten(transformations.colorize(self.config.tonecolors, transformations.tonesandhi(self.config.dictionary.tonedchars(expression))))

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
            return pinyin.flatten(meanings[0])
    
    def weblinkgeneration(self, expression):
        # Generate a list of links to online dictionaries, etc to query the expression
        return " ".join(['[<a href="' + urltemplate.replace("{searchTerms}", utils.urlescape(expression)) + '" title="' + tooltip + '">' + text + '</a>]' for text, tooltip, urltemplate in self.config.weblinks])

    #
    # Core updater routines
    #
    
    def getdictreading(self, expression):
        dictreadingsources = [
                # Get the reading by considering the text as a (Western) number
                lambda: numbers.readingfromnumberlike(expression, self.config.dictionary),
                # Use CEDICT to get reading (always succeeds)
                lambda: self.config.dictionary.reading(expression)
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
                     lambda: self.config.dictionary.meanings(expression, self.config.prefersimptrad)),
                    # Interpret Hanzi as numbers. NB: only consult after CEDICT so that we
                    # handle curious numbers such as 'liang' using the dictionary
                    (None,
                     lambda: (numbers.meaningfromnumberlike(expression, self.config.dictionary), None))
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


if __name__ == "__main__":
    import copy
    import unittest
    
    import config
    from mocks import *
    from utils import Thunk
    
    # Shared dictionary
    englishdict = Thunk(lambda: dictionary.PinyinDictionary.load("en"))
    
    class FieldUpdaterFromAudioTest(unittest.TestCase):
        def testDoesntDoAnythingWhenDisabled(self):
            self.assertEquals(self.updatefact(u"hen3 hao3", { "audio" : "", "expression" : "junk" }, forcepinyininaudiotosoundtags = False),
                              { "audio" : "", "expression" : "junk" })
        
        def testWorksIfFieldMissing(self):
            self.assertEquals(self.updatefact(u"hen3 hao3", { "expression" : "junk" }, forcepinyininaudiotosoundtags = True),
                              { "expression" : "junk" })

        def testLeavesOtherFieldsAlone(self):
            self.assertEquals(self.updatefact(u"", { "audio" : "junk", "expression" : "junk" }, forcepinyininaudiotosoundtags = True),
                              { "audio" : u"", "expression" : "junk" })

        def testReformatsAccordingToConfig(self):
            henhaoaudio = u"[sound:" + os.path.join("Test", "hen3.mp3") + "][sound:" + os.path.join("Test", "hao3.mp3") + "]"

            self.assertEquals(
                self.updatefact(u"hen3 hao3", { "audio" : "junky" }, forcepinyininaudiotosoundtags = True),
                { "audio" : henhaoaudio })
            self.assertEquals(
                self.updatefact(u"hen3,hǎo", { "audio" : "junky" }, forcepinyininaudiotosoundtags = True),
                { "audio" : henhaoaudio })
        
        def testDoesntModifySoundTags(self):
            self.assertEquals(
                self.updatefact(u"[sound:aeuth34t0914bnu.mp3][sound:ae390n32uh2ub.mp3]", { "audio" : "" }, forcepinyininaudiotosoundtags = True),
                { "audio" : u"[sound:aeuth34t0914bnu.mp3][sound:ae390n32uh2ub.mp3]" })
            self.assertEquals(
                self.updatefact(u"[sound:hen3.mp3][sound:hao3.mp3]", { "audio" : "" }, forcepinyininaudiotosoundtags = True),
                { "audio" : u"[sound:hen3.mp3][sound:hao3.mp3]" })
        
        # Test helpers
        def updatefact(self, *args, **kwargs):
            infos, fact = self.updatefactwithinfos(*args, **kwargs)
            return fact

        def updatefactwithinfos(self, audio, fact, mediapacks = None, **kwargs):
            notifier = MockNotifier()

            if mediapacks == None:
                mediapacks = [media.MediaPack("Test", { "shu1.mp3" : "shu1.mp3", "shu1.ogg" : "shu1.ogg",
                                                        "san1.mp3" : "san1.mp3", "qi1.ogg" : "qi1.ogg", "Kai1.mp3" : "location/Kai1.mp3",
                                                        "hen3.mp3" : "hen3.mp3", "hen2.mp3" : "hen2.mp3", "hao3.mp3" : "hao3.mp3" })]
            mediamanager = MockMediaManager(mediapacks)

            factclone = copy.deepcopy(fact)
            FieldUpdaterFromAudio(notifier, mediamanager, config.Config(kwargs)).updatefact(factclone, audio)

            return notifier.infos, factclone
    
    class FieldUpdaterFromMeaningTest(unittest.TestCase):
        def testDoesntDoAnythingWhenDisabled(self):
            self.assertEquals(self.updatefact(u"(1) yes (2) no", { "meaning" : "", "expression" : "junk" }, forcemeaningnumberstobeformatted = False),
                              { "meaning" : "", "expression" : "junk" })
        
        def testWorksIfFieldMissing(self):
            self.assertEquals(self.updatefact(u"(1) yes (2) no", { "expression" : "junk" }, forcemeaningnumberstobeformatted = True),
                              { "expression" : "junk" })

        def testLeavesOtherFieldsAlone(self):
            self.assertEquals(self.updatefact(u"", { "meaning" : "junk", "expression" : "junk" }, forcemeaningnumberstobeformatted = True),
                              { "meaning" : u"", "expression" : "junk" })

        def testReformatsAccordingToConfig(self):
            self.assertEquals(
                self.updatefact(u"(1) yes (2) no", { "meaning" : "junky" },
                    forcemeaningnumberstobeformatted = True, meaningnumbering = "circledArabic", colormeaningnumbers = False),
                    { "meaning" : u"① yes ② no" })
            self.assertEquals(
                self.updatefact(u"(10) yes 2 no", { "meaning" : "junky" },
                    forcemeaningnumberstobeformatted = True, meaningnumbering = "none", colormeaningnumbers = False),
                    { "meaning" : u" yes 2 no" })
        
        # Test helpers
        def updatefact(self, reading, fact, **kwargs):
            factclone = copy.deepcopy(fact)
            FieldUpdaterFromMeaning(config.Config(kwargs)).updatefact(factclone, reading)
            return factclone
    
    class FieldUpdaterFromReadingTest(unittest.TestCase):
        def testDoesntDoAnythingWhenDisabled(self):
            self.assertEquals(self.updatefact(u"hen3 hǎo", { "reading" : "", "expression" : "junk" }, forcereadingtobeformatted = False),
                              { "reading" : "", "expression" : "junk" })
        
        def testDoesSomethingWhenDisabledIfAlways(self):
            fact = { "reading" : "", "expression" : "junk" }
            FieldUpdaterFromReading(config.Config({ "forcereadingtobeformatted" : False })).updatefactalways(fact, u"also junk")
            self.assertEquals(fact, { "reading" : "also junk", "expression" : "junk" })
        
        def testWorksIfFieldMissing(self):
            self.assertEquals(self.updatefact(u"hen3 hǎo", { "expression" : "junk" }, forcereadingtobeformatted = True),
                              { "expression" : "junk" })

        def testLeavesOtherFieldsAlone(self):
            self.assertEquals(self.updatefact(u"", { "reading" : "junk", "expression" : "junk" }, forcereadingtobeformatted = True),
                              { "reading" : u"", "expression" : "junk" })

        def testReformatsAccordingToConfig(self):
            self.assertEquals(
                self.updatefact(u"hen3 hǎo", { "reading" : "junky" },
                    forcereadingtobeformatted = True, tonedisplay = "tonified",
                    colorizedpinyingeneration = True, tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"]),
                    { "reading" : u'<span style="color:#333333">hěn</span> <span style="color:#333333">hǎo</span>' })
        
        # Test helpers
        def updatefact(self, reading, fact, **kwargs):
            factclone = copy.deepcopy(fact)
            FieldUpdaterFromReading(config.Config(kwargs)).updatefact(factclone, reading)
            return factclone
    
    class FieldUpdaterFromExpressionTest(unittest.TestCase):
        def testAutoBlanking(self):
            self.assertEquals(self.updatefact(u"", { "reading" : "blather", "meaning" : "junk", "color" : "yes!", "trad" : "meh", "simp" : "yay" }),
                              { "reading" : "", "meaning" : "", "color" : "", "trad" : "", "simp" : "" })
        
        def testAutoBlankingAudioMeasureWord(self):
            # TODO: test behaviour for audio and measure word, once we know what it should be
            pass
        
        def testFullUpdate(self):
            self.assertEquals(
                self.updatefact(u"书", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "trad" : "", "simp" : "" },
                    colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True,
                    tonedisplay = "tonified", meaningnumbering = "circledChinese", colormeaningnumbers = False, meaningseperator = "lines", prefersimptrad = "simp",
                    audiogeneration = True, audioextensions = [".mp3"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], weblinkgeneration = False, hanzimasking = False,
                    tradgeneration = True, simpgeneration = True, forceexpressiontobesimptrad = False), {
                        "reading" : u'<span style="color:#ff0000">shū</span>',
                        "meaning" : u'㊀ book<br />㊁ letter<br />㊂ same as <span style="color:#ff0000">\u4e66</span><span style="color:#ff0000">\u7ecf</span> Book of History',
                        "mw" : u'<span style="color:#00aa00">本</span> - <span style="color:#00aa00">běn</span>, <span style="color:#0000ff">册</span> - <span style="color:#0000ff">cè</span>, <span style="color:#0000ff">部</span> - <span style="color:#0000ff">bù</span>, <span style="color:#ffaa00">丛</span> - <span style="color:#ffaa00">cóng</span>',
                        "audio" : u"[sound:" + os.path.join("Test", "shu1.mp3") + "]",
                        "color" : u'<span style="color:#ff0000">书</span>',
                        "trad" : u"書", "simp" : u"书"
                      })
        
        def testFullUpdateGerman(self):
            self.assertEquals(
                self.updatefact(u"书", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "trad" : "", "simp" : "" },
                    dictlanguage = "de",
                    colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True,
                    tonedisplay = "tonified", audiogeneration = True, audioextensions = [".ogg"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"],
                    tradgeneration = True, simpgeneration = True, forceexpressiontobesimptrad = False), {
                        "reading" : u'<span style="color:#ff0000">shū</span>',
                        "meaning" : u'Buch, Geschriebenes (S)',
                        "mw" : u'',
                        "audio" : u"[sound:" + os.path.join("Test", "shu1.ogg") + "]",
                        "color" : u'<span style="color:#ff0000">书</span>',
                        "trad" : u"書", "simp" : u"书"
                      })
        
        def testUpdatePreservesWhitespace(self):
            self.assertEquals(
                self.updatefact(u"\t书", { "reading" : "", "color" : "", "trad" : "", "simp" : "" },
                    dictlanguage = "en",
                    colorizedpinyingeneration = False, colorizedcharactergeneration = True, meaninggeneration = False,
                    tonedisplay = "tonified", audiogeneration = False, tradgeneration = True, simpgeneration = True, forceexpressiontobesimptrad = False), {
                        "reading" : u'\tshū',
                        "color" : u'\t<span style="color:#ff0000">书</span>',
                        # TODO: make the simp and trad fields preserve whitespace by moving away from Google Translate as the translator
                        "trad" : u"書", "simp" : u"书"
                      })
        
        def testDontOverwriteFields(self):
            self.assertEquals(
                self.updatefact(u"书", { "reading" : "a", "meaning" : "b", "mw" : "c", "audio" : "d", "color" : "e", "trad" : "f", "simp" : "g" },
                    colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True,
                    tonedisplay = "tonified", meaningnumbering = "circledChinese", meaningseperator = "lines", prefersimptrad = "simp",
                    audiogeneration = True, audioextensions = [".mp3"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], weblinkgeneration = True,
                    tradgeneration = True, simpgeneration = True), {
                        "reading" : "a", "meaning" : "b", "mw" : "c", "audio" : "d", "color" : "e", "trad" : "f", "simp" : "g"
                      })
        
        def testUpdateExpressionItself(self):
            self.assertEquals(
                self.updatefact(u"啤酒", { "expression" : "" },
                    colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False,
                    detectmeasurewords = False, audiogeneration = False, weblinkgeneration = False), { "expression" : u"啤酒" })
        
        def testUpdateMeaningAndMWWithoutMWField(self):
            self.assertEquals(
                self.updatefact(u"啤酒", { "expression" : "", "meaning" : "" },
                    colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = True,
                    meaningnumbering = "circledChinese", colormeaningnumbers = False, detectmeasurewords = True, audiogeneration = False, weblinkgeneration = False,
                    forceexpressiontobesimptrad = False), {
                        "expression" : u"啤酒", "meaning" : u"㊀ beer<br />㊁ MW: 杯 - b\u0113i, 瓶 - p\xedng, 罐 - gu\xe0n, 桶 - t\u01d2ng, 缸 - g\u0101ng"
                      })

        def testMeaningHanziMasking(self):
            self.assertEquals(
                self.updatefact(u"书", { "meaning" : "" },
                    colorizedpinyingeneration = True, colorizedcharactergeneration = False, meaninggeneration = True, detectmeasurewords = False,
                    tonedisplay = "tonified", meaningnumbering = "circledArabic", colormeaningnumbers = True, meaningnumberingcolor="#123456", meaningseperator = "custom", custommeaningseperator = " | ", prefersimptrad = "simp",
                    audiogeneration = True, audioextensions = [".mp3"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], weblinkgeneration = False, hanzimasking = True, hanzimaskingcharacter = "MASKED"), {
                        "meaning" : u'<span style="color:#123456">①</span> book | <span style="color:#123456">②</span> letter | <span style="color:#123456">③</span> same as <span style="color:#123456">MASKED</span><span style="color:#ff0000">\u7ecf</span> Book of History | <span style="color:#123456">④</span> MW: <span style="color:#00aa00">本</span> - <span style="color:#00aa00">běn</span>, <span style="color:#0000ff">册</span> - <span style="color:#0000ff">cè</span>, <span style="color:#0000ff">部</span> - <span style="color:#0000ff">bù</span>, <span style="color:#ffaa00">丛</span> - <span style="color:#ffaa00">cóng</span>',
                      })

        def testMeaningSurnameMasking(self):
            self.assertEquals(
                self.updatefact(u"汪", { "meaning" : "" },
                    meaninggeneration = True, meaningnumbering = "arabicParens", colormeaningnumbers = False, meaningseperator = "lines"), {
                        "meaning" : u'(1) expanse of water<br />(2) ooze<br />(3) (a surname)',
                      })

        def testMeaningChineseNumbers(self):
            self.assertEquals(self.updatefact(u"九千零二十五", { "meaning" : "" }, meaninggeneration = True), { "meaning" : u'9025' })

        def testMeaningWesternNumbersYear(self):
            self.assertEquals(self.updatefact(u"2001年", { "meaning" : "" }, meaninggeneration = True), { "meaning" : u'2001AD' })

        def testUpdateReadingOnly(self):
            self.assertEquals(
                self.updatefact(u"啤酒", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                    colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False,
                    detectmeasurewords = False, audiogeneration = False, tonedisplay = "numeric", weblinkgeneration = False), {
                        "reading" : u'pi2 jiu3', "meaning" : "", "mw" : "", "audio" : "", "color" : ""
                      })
        
        def testUpdateReadingAndMeaning(self):
            self.assertEquals(
                self.updatefact(u"㝵", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : "" },
                    colorizedpinyingeneration = True, colorizedcharactergeneration = False, meaninggeneration = True, detectmeasurewords = False, tonedisplay = "numeric",
                    meaningnumbering = "arabicParens", colormeaningnumbers = True, meaningnumberingcolor = "#123456", meaningseperator = "commas", prefersimptrad = "trad",
                    audiogeneration = False, tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], weblinkgeneration = False), {
                        "reading" : u'<span style="color:#ffaa00">de2</span>',
                        "meaning" : u'<span style="color:#123456">(1)</span> to obtain, <span style="color:#123456">(2)</span> archaic variant of <span style="color:#ffaa00">得</span> - <span style="color:#ffaa00">de2</span>, <span style="color:#123456">(3)</span> component in <span style="color:#0000ff">礙</span> - <span style="color:#0000ff">ai4</span> and <span style="color:#ffaa00">鍀</span> - <span style="color:#ffaa00">de2</span>',
                        "mw" : "", "audio" : "", "color" : "", "weblinks" : ""
                      })
        
        def testUpdateReadingAndMeasureWord(self):
            self.assertEquals(
                self.updatefact(u"丈夫", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : "" },
                    colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = True,
                    tonedisplay = "numeric", prefersimptrad = "trad", audiogeneration = False, weblinkgeneration = False), {
                        "reading" : u'zhang4 fu', "meaning" : u'',
                        "mw" : u"個 - ge4", "audio" : "", "color" : "", "weblinks" : ""
                      })
        
        def testUpdateReadingAndAudio(self):
            self.assertEquals(
                self.updatefact(u"三七開", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : "" },
                    colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = False,
                    tonedisplay = "tonified", audiogeneration = True, audioextensions = [".mp3", ".ogg"], weblinkgeneration = False), {
                        "reading" : u'sān qī kāi', "meaning" : u'', "mw" : "",
                        "audio" : u"[sound:" + os.path.join("Test", "san1.mp3") + "]" +
                                  u"[sound:" + os.path.join("Test", "qi1.ogg") + "]" +
                                  u"[sound:" + os.path.join("Test", "location/Kai1.mp3") + "]",
                        "color" : "", "weblinks" : ""
                      })
        
        def testUpdateReadingAndColoredHanzi(self):
            self.assertEquals(
                self.updatefact(u"三峽水库", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : u"" },
                    dictlanguage = "pinyin", colorizedpinyingeneration = False, colorizedcharactergeneration = True, meaninggeneration = False, detectmeasurewords = False,
                    tonedisplay = "numeric", audiogeneration = False, tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"], weblinkgeneration = False), {
                        "reading" : u'san1 xia2 shui3 ku4', "meaning" : u'', "mw" : "", "audio" : "",
                        "color" : u'<span style="color:#111111">三</span><span style="color:#222222">峽</span><span style="color:#333333">水</span><span style="color:#444444">库</span>', "weblinks" : ""
                      })
        
        def testUpdateReadingAndLinks(self):
            self.assertEquals(
                self.updatefact(u"一概", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : "Yes, I get overwritten!" },
                    colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = False,
                    tonedisplay = "numeric", audiogeneration = False, tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"],
                    weblinkgeneration = True, weblinks = [("YEAH!", "mytitle", "silly{searchTerms}url"), ("NAY!", "myothertitle", "verysilly{searchTerms}url")]), {
                        "reading" : u'yi1 gai4', "meaning" : u'', "mw" : "", "audio" : "", "color" : u'',
                        "weblinks" : u'[<a href="silly%E4%B8%80%E6%A6%82url" title="mytitle">YEAH!</a>] [<a href="verysilly%E4%B8%80%E6%A6%82url" title="myothertitle">NAY!</a>]'
                      })

        def testWebLinkFieldCanBeMissingAndStaysMissing(self):
            self.assertEquals(self.updatefact(u"一概", { }, weblinkgeneration = True), { })
        
        def testWebLinksNotBlankedIfDisabled(self):
            self.assertEquals(self.updatefact(u"一概", { "weblinks": "Nope!" }, weblinkgeneration = False), { "weblinks" : "Nope!" })
        
        def testReadingFromWesternNumbers(self):
            self.assertEquals(self.updatefact(u"111", { "reading" : "" }, colorizedpinyingeneration = True, tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"]),
                                                      { "reading" : u'<span style="color:#333333">b\u01cei</span> <span style="color:#111111">y\u012b</span> <span style="color:#222222">sh\xed</span> <span style="color:#111111">y\u012b</span>' })
        
        def testNotifiedUponAudioGenerationWithNoPacks(self):
            infos, fact = self.updatefactwithinfos(u"三月", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                                mediapacks = [],
                                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = False,
                                tonedisplay = "numeric", audiogeneration = True)
            
            self.assertEquals(fact, { "reading" : u'san1 yue4', "meaning" : u'', "mw" : "", "audio" : "", "color" : "" })
            self.assertEquals(len(infos), 1)
            self.assertTrue("cannot" in infos[0])
        
        def testUpdateMeasureWordAudio(self):
            mwaudio = self.updatefact(u"啤酒", { "mwaudio" : "" }, detectmeasurewords = False, mwaudiogeneration = True, audioextensions = [".mp3", ".ogg"])["mwaudio"]
            for quantitydigit in ["yi1", "liang3", "liang2", "san1", "si4", "wu3", "wu2", "liu4", "qi1", "ba1", "jiu3", "jiu2", "ji3", "ji2"]:
                mwaudio = mwaudio.replace(quantitydigit, "X")
            
            # jiu3 in the numbers aliases with jiu3 in the characters :(
            sounds = ["X", "bei1", "pi2", "X",
                      "X", "ping2", "pi2", "X",
                      "X", "guan4", "pi2", "X",
                      "X", "tong3", "pi2", "X",
                      "X", "gang1", "pi2", "X"]
            self.assertEquals(mwaudio, "".join([u"[sound:" + os.path.join("MWAudio", sound + ".mp3") + "]" for sound in sounds]))

        def testFallBackOnGoogleForPhrase(self):
            self.assertEquals(
                self.updatefact(u"你好，你是我的朋友吗", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                    fallbackongoogletranslate = True,
                    colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = True, detectmeasurewords = False,
                    tonedisplay = "numeric", audiogeneration = False, hanzimasking = False), {
                        "reading" : u'ni3 hao3, ni3 shi4 wo3 de peng2 you ma',
                        "meaning" : u'Hello, you are right my friend<br /><span style="color:gray"><small>[Google Translate]</small></span><span> </span>',
                        "mw" : "", "audio" : "", "color" : ""
                      })

        def testUpdateSimplifiedTraditional(self):
            self.assertEquals(
                self.updatefact(u"个個", { "simp" : "", "trad" : "" },
                    simpgeneration = True, tradgeneration = True), {
                        "simp"  : u"个个",
                        "trad" : u"個個"
                      })

        def testUpdateSimplifiedTraditionalDoesNothingIfSimpTradIdentical(self):
            self.assertEquals(
                self.updatefact(u"鼠", { "simp" : "", "trad" : "" }, simpgeneration = True, tradgeneration = True), { "simp"  : u"", "trad" : u"" })

        def testOverwriteExpressionWithSimpTrad(self):
            self.assertEquals(self.updatefact(u"个個", { "expression" : "" }, forceexpressiontobesimptrad = True, prefersimptrad = "trad"),
                                                     { "expression"  : u"個個" })

            self.assertEquals(self.updatefact(u"个個", { "expression" : "" }, forceexpressiontobesimptrad = True, prefersimptrad = "simp"),
                                                     { "expression"  : u"个个" })

        def testOverwriteExpressionWithSimpTradEvenWorksIfFieldFilled(self):
            self.assertEquals(self.updatefact(u"个個", { "expression" : "I'm Filled!" }, forceexpressiontobesimptrad = True, prefersimptrad = "trad"),
                                                     { "expression"  : u"個個" })

        def testOverwriteExpressionWithSimpTradCausesColoredCharsToUpdateEvenIfFilled(self):
            self.assertEquals(
                self.updatefact(u"个個", { "expression" : "I'm Filled!", "color" : "dummy" },
                                forceexpressiontobesimptrad = True, prefersimptrad = "trad", tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"]),
                                { "expression"  : u"個個", "color" : u'<span style="color:#444444">個</span><span style="color:#444444">個</span>' })

        def testDontOverwriteFilledColoredCharactersIfSimpTradDoesntChange(self):
            self.assertEquals(
                self.updatefact(u"個個", { "expression" : "I'm Filled!", "color" : "dummy" },
                                forceexpressiontobesimptrad = True, prefersimptrad = "trad", tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"]),
                                { "expression"  : u"個個", "color" : "dummy" })

        def testUpdateReadingAndColoredHanziAndAudioWithSandhi(self):
            self.assertEquals(
                self.updatefact(u"很好", { "reading" : "", "color" : "", "audio" : "" },
                    colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = False,
                    detectmeasurewords = False, audiogeneration = True, audioextensions = [".mp3"], tonedisplay = "numeric",
                    tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"], weblinkgeneration = False), {
                        "reading" : u'<span style="color:#66cc66">hen3</span> <span style="color:#00aa00">hao3</span>',
                        "color" : u'<span style="color:#66cc66">很</span><span style="color:#00aa00">好</span>',
                        "audio" : u"[sound:" + os.path.join("Test", "hen2.mp3") + "]" +
                                  u"[sound:" + os.path.join("Test", "hao3.mp3") + "]"
                      })
        
        # Test helpers
        def updatefact(self, *args, **kwargs):
            infos, fact = self.updatefactwithinfos(*args, **kwargs)
            return fact
        
        def updatefactwithinfos(self, expression, fact, mediapacks = None, **kwargs):
            notifier = MockNotifier()
            
            if mediapacks == None:
                mediapacks = [media.MediaPack("Test", { "shu1.mp3" : "shu1.mp3", "shu1.ogg" : "shu1.ogg",
                                                        "san1.mp3" : "san1.mp3", "qi1.ogg" : "qi1.ogg", "Kai1.mp3" : "location/Kai1.mp3",
                                                        "hen3.mp3" : "hen3.mp3", "hen2.mp3" : "hen2.mp3", "hao3.mp3" : "hao3.mp3" }),
                              media.MediaPack("MWAudio", { "pi2.mp3" : "pi2.mp3", "jiu3.mp3" : "jiu3.mp3",
                                                           "bei1.mp3" : "bei1.mp3", "ping2.mp3" : "ping2.mp3", "guan4.mp3" : "guan4.mp3", "tong3.mp3" : "tong3.mp3", "gang1.mp3" : "gang1.mp3",
                                                           "yi1.mp3" : "yi1.mp3", "liang3.mp3" : "liang3.mp3", "san1.mp3" : "san1.mp3", "si4.mp3" : "si4.mp3", "wu3.mp3" : "wu3.mp3",
                                                           "liu4.mp3" : "liu4.mp3", "qi1.mp3" : "qi1.mp3", "ba1.mp3" : "ba1.mp3", "jiu3.mp3" : "jiu3.mp3", "ji3.mp3" : "ji3.mp3",
                                                           # Sandhi variants of numerals:
                                                           "wu2.mp3" : "wu2.mp3", "jiu2.mp3" : "jiu2.mp3", "ji2.mp3" : "ji2.mp3" })
                             ]
            mediamanager = MockMediaManager(mediapacks)
            
            factclone = copy.deepcopy(fact)
            FieldUpdaterFromExpression(notifier, mediamanager, config.Config(utils.updated({ "dictlanguage" : "en" }, kwargs))).updatefact(factclone, expression)
            
            return notifier.infos, factclone
    
    unittest.main()
