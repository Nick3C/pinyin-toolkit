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


class FieldUpdater(object):
    def __init__(self, notifier, mediamanager, config):
        self.notifier = notifier
        self.mediamanager = mediamanager
        self.config = config
    
    def preparetokens(self, tokens):
        if self.config.colorizedpinyingeneration:
            tokens = transformations.colorize(self.config.tonecolors, tokens)
    
        return pinyin.flatten(tokens, tonify=self.config.shouldtonify)
    
    #
    # Generation
    #
    
    def generatereading(self, dictreading):
        # Put pinyin into lowercase before anything else is done to it
        # TODO: do we really want lower case here? If so, we should do it for colorized pinyin as well.
        return self.preparetokens(dictreading).lower()
    
    def generateaudio(self, dictreading):
        mediapacks = self.mediamanager.discovermediapacks()
        if len(mediapacks) == 0:
            # Show a warning the first time we detect that we're missing a sound pack
            self.notifier.infoOnce("The Pinyin Toolkit cannot find an audio pack for text-to-speech.  We reccomend you either disable the audio functionality "
                                   + "or install the free Chinese-Lessons.com Mandarin Sounds audio pack using the Audio tab in Tool > Preferences.")
            
            # There is no way we can generate an audio reading with no packs - give up
            return None
        
        # Get the best media pack to generate the audio, along with the string of files from that pack we need to take
        mediapack, output, _mediamissing = transformations.PinyinAudioReadings(mediapacks, self.config.audioextensions).audioreading(dictreading)
        
        # Construct the string of audio tags from the optimal choice of sounds
        output_tags = u""
        for outputfile in output:
            # Install required media in the deck as we go, getting the canonical string to insert into the sound field upon installation
            output_tags += "[sound:%s]" % self.mediamanager.importtocurrentdeck(os.path.join(mediapack.packpath, outputfile))
        
        return output_tags
    
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
        meanings = [meaning for meaning in [self.preparetokens(dictmeaning) for dictmeaning in dictmeanings] if meaning.strip != '']
        
        if len(meanings) == 0:
            # After flattening and stripping, we didn't get any meanings: don't update the field
            return None
        
        # Use the configuration to insert numbering etc
        return self.config.formatmeanings(meanings)
    
    def generatemeasureword(self, dictmeasurewords):
        if dictmeasurewords == None or len(dictmeasurewords) == 0:
            # No measure word, so don't update the field
            return None
        
        # Just use the first measure word meaning, if there was more than one
        return self.preparetokens(dictmeasurewords[0])
    
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
    # Core updater routine
    #
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
            return # give up after auto-blanking [removes minor delay]
        
        expressionupdated=False    
        # Figure out the reading for the expression field, with sandhi considered
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
                break
  
        # Apply tone sandhi: this information is needed both by the sound generation
        # and the colorisation, so we can't do it in generatereading
        dictreading = transformations.tonesandhi(dictreading)
  
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
                dictmeanings, dictmeasurewords = dictionary.combinemeaningsmws(dictmeanings, dictmeasurewords), None
            
            # NB: expression only used for Hanzi masking here
            meaning = self.generatemeanings(expression, dictmeanings)
            if meaning and dictmeaningssource:
                # Append attribution to the meaning if we have any
                meaning = meaning + dictmeaningssource
            
            # DEBUG: Nick wants to do something with audio for measure words here?
            # yes, want the measure word to appear as:
            #       [MW1] - [MWPY1]
            #       [MW2] - [MWPY2]
            #       [sound:mw1][sound:mw2]
            # The measure word shouldn't be included on the main card because if so you break min-info rule (harder to learn it)
            #' If testing seperately then putting audio in the MW field is a good idea (so it will play when the measure word question is answered)

        # Generate translations of the expression into simplified/traditional on-demand
        expressionviews = utils.FactoryDict(lambda simptrad: self.generateincharactersystem(expression, simptrad))
        # If trad=simp then wipe them to prevent unwanted form-fill and unwanted card-generation
        if expressionviews['simp']==expressionviews['trad']:
            expressionviews['simp'] = u""
            expressionviews['trad'] = u""
        
        # Update the expression is option is turned on and the preference simp/trad is different to expression (i.e. needs correcting)
        if (self.config.forceexpressiontobesimptrad) and (expressionviews[self.config.prefersimptrad]) and (expressionviews[self.config.prefersimptrad].strip() != expression) and (expression != expressionviews[self.config.prefersimptrad]):
            expression = expressionviews[self.config.prefersimptrad]
            expressionupdated=True

        # Do the updates on the fields the user has requested:
        # NB: when adding an updater to this list, make sure that you have
        # added it to the updatecontrolflags dictionary in Config as well!
        updaters = {
                'expression' : lambda: expression,
                'reading'    : lambda: self.generatereading(dictreading),
                'meaning'    : lambda: meaning,
                'mw'         : lambda: self.generatemeasureword(dictmeasurewords),
                'audio'      : lambda: self.generateaudio(dictreading),
                'color'      : lambda: self.generatecoloredcharacters(expression),
                'trad'       : lambda: expressionviews["trad"],
                'simp'       : lambda: expressionviews["simp"],
                'weblinks'   : lambda: self.weblinkgeneration(expression)
            }

        # Loop through each field, deciding whether to update it or not
        for key, updater in updaters.items():
            # if there is no key or this option has been disabled then stop 
            if not (key in fact) or not (config.updatecontrolflags[key]):
                continue
            else:
                enabled = True
                            
            # Turn off the update if the field is not empty already (so we don't overwrite it)...
            if (fact[key].strip() != u""):
                enabled=False
            
            
            # ... unless:
            # 1) this is the expression field      because it should be over-written with simp/trad)
            # 2) this is the weblinks field        because must always be up to date
            if (key == "expression") or (key=="weblinks"):
                enabled = True
                
            # 3) (this is the simp/trad field ) AND (there are no simp/trad meaning)
            if ((key == "trad") and (expressionviews['trad']=="")) or ((key == "simp") and (expressionviews['simp']=="")):
                enabled = True
                # trad must not do this all the time or corrections can be lost
                # the only 'safe' condition is where simp/trad ceases to be present in expression

            # 4) if this is the color field and expression has been updated / force over-written (i.e. simp/trad didn't match)
            if (key == "color") and (expressionupdated):
                enabled = True
                # color must not do this all the time or tone can be lost.
                # the only 'safe' condition is when simp/trad don't match

            # 5) for the pinyin field, if colorfromblackwhite is turned on and the only change is formating
            #if (key == "pinyin") and (self.config.colorfromblackwhite) and ( (stripdown(reading) ) == (stripdown(fact['reading']) ) ):
            #    enabled = True



            # If still enabled then fill the field with the new value
            if (enabled): 
                value = updater()
                if value != None and value != fact[key]:
                    fact[key] = value


def stripdown(what):
    return utils.striphtml(what)
    

if __name__ == "__main__":
    import copy
    import unittest
    
    import config
    from mocks import *
    from utils import Thunk
    
    # Shared dictionary
    englishdict = Thunk(lambda: dictionary.PinyinDictionary.load("en"))
    
    class FieldUpdaterTest(unittest.TestCase):
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

        def testReadingFromWesternNumbers(self):
            self.assertEquals(self.updatefact(u"111", { "reading" : "" }, colorizedpinyingeneration = True, tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"]),
                                                      { "reading" : u'<span style="color:#333333">b\u01cei</span> <span style="color:#111111">y\u012b</span> <span style="color:#222222">sh\xed</span> <span style="color:#111111">y\u012b</span>' })
        
        def testWebLinkFieldCanBeMissingAndStaysMissing(self):
            self.assertEquals(self.updatefact(u"一概", { }, weblinkgeneration = True), { })
        
        def testWebLinksNotBlankedIfDisabled(self):
            self.assertEquals(self.updatefact(u"一概", { "weblinks": "Nope!" }, weblinkgeneration = False), { "weblinks" : "Nope!" })
        
        def testNotifiedUponAudioGenerationWithNoPacks(self):
            infos, fact = self.updatefactwithinfos(u"三月", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                                mediapacks = [],
                                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = False,
                                tonedisplay = "numeric", audiogeneration = True)
            
            self.assertEquals(fact, { "reading" : u'san1 yue4', "meaning" : u'', "mw" : "", "audio" : "", "color" : "" })
            self.assertEquals(len(infos), 1)
            self.assertTrue("cannot" in infos[0])
        
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

        def testOverwriteExpressionWithSimpTrad(self):
            self.assertEquals(self.updatefact(u"个個", { "expression" : "" }, forceexpressiontobesimptrad = True, prefersimptrad = "trad"),
                                                     { "expression"  : u"個個" })

            self.assertEquals(self.updatefact(u"个個", { "expression" : "" }, forceexpressiontobesimptrad = True, prefersimptrad = "simp"),
                                                     { "expression"  : u"个个" })

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
                                                        "hen3.mp3" : "hen3.mp3", "hen2.mp3" : "hen2.mp3", "hao3.mp3" : "hao3.mp3" })]
            mediamanager = MockMediaManager(mediapacks)
            
            factclone = copy.deepcopy(fact)
            FieldUpdater(notifier, mediamanager, config.Config(utils.updated({ "dictlanguage" : "en" }, kwargs))).updatefact(factclone, expression)
            
            return notifier.infos, factclone
    
    unittest.main()
