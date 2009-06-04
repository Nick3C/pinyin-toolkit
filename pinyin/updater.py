#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import dictionary
import dictionaryonline
import media
import meanings
import pinyin
import transformations

from logger import log


class FieldUpdater(object):
    def __init__(self, notifier, mediamanager, config, dictionary):
        self.notifier = notifier
        self.mediamanager = mediamanager
        self.config = config
        self.dictionary = dictionary
    
    def preparetokens(self, tokens):
        if self.config.colorizedpinyingeneration:
            tokens = transformations.Colorizer(self.config.tonecolors).colorize(tokens)
    
        return tokens.flatten(tonify=self.config.shouldtonify)
    
    #
    # Media discovery
    #
    
    # def discoverlegacymedia(self):
    #         # NB: we used to do this when initialising the toolkit, but that dosen't work,
    #         # for the simple reason that if you change deck the media should change, but
    #         # we can't hook that event
    #         
    #         # I can ask Damien for a hook if you like. He has been very good with these sort of things in the past.
    #         
    #         # Discover all the files in the media directory
    #         mediaDir = self.mw.deck.mediaDir()
    #         if mediaDir:
    #             try:
    #                 mediadircontents = os.listdir(mediaDir)
    #             except IOError:
    #                 log.exception("Error while listing media directory")
    #                 mediadircontents = None
    #         else:
    #             log.info("The media directory was either not present or not accessible")
    #             mediadircontents = None
    #         
    #         # Finally, find any legacy media in that directory. TODO: use this method for something
    #         return media.discoverlegacymedia(mediadircontents, self.mw.deck.s.all("select originalPath, filename from media"))
    
    #
    # Generation
    #
    
    def generatereading(self, dictreading):
        # TODO: do we really want lower case here? If so, we should do it for colorized pinyin as well.
        return self.preparetokens(dictreading).lower() # Put pinyin into lowercase before anything else is done to it
    
    def generateaudio(self, dictreading):
        mediapacks = self.mediamanager.discovermediapacks()
        if len(mediapacks) == 0:
            # Show a warning the first time we detect that we're missing a sound pack
            self.notifier.infoOnce("We appear to be missing some audio samples. This might be our fault, but if you haven't already done so, "
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
            output_tags += "[sound:%s]" % self.mediamanager.importtocurrentdeck(os.path.join(mediapack.packpath, outputfile))
        
        return output_tags
    
    def generatemeanings(self, dictmeanings):
        if dictmeanings == None:
            # We didn't get any meanings, don't update the field
            return None
        
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
        return transformations.Colorizer(self.config.tonecolors).colorize(self.dictionary.tonedchars(expression)).flatten()
    
    #
    # Core updater routine
    #
    
    def updatefact(self, fact, expression):
        # AutoBlanking Feature - If there is no expression, zeros relevant fields
        # DEBUG - add feature to store the text when a lookup is performed. When new text is entered then allow auto-blank any field that has not been edited
        if expression == None or expression.strip() == u"":
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
            # longest MW should be: "? - zhangì (9 char)
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
                translation = dictionaryonline.gTrans(expression, self.config.dictlanguage)
                
                # Only fill out the meanings field if we get something useful back
                if translation != None:
                    dictmeanings = [pinyin.TokenList([translation])]

    
            # DEBUG: Nick wants to do something with audio for measure words here?
            # " [sound:MW]" # DEBUG - pass to audio loop
    
        # Do the updates on the fields the user has requested:
        updaters = {
                'expression' : (True,                                     lambda: expression),
                'reading'    : (True,                                     lambda: self.generatereading(dictreading)),
                'meaning'    : (self.config.meaninggeneration,            lambda: self.generatemeanings(dictmeanings)),
                'mw'         : (self.config.detectmeasurewords,           lambda: self.generatemeasureword(dictmeasurewords)),
                'audio'      : (self.config.audiogeneration,              lambda: self.generateaudio(dictreading)),
                'color'      : (self.config.colorizedcharactergeneration, lambda: self.generatecoloredcharacters(expression))
            }
    
        for key, (enabled, updater) in updaters.items():
            # Skip updating if no suitable field, we are disabled, or the field has text
            if not(key in fact) or not(enabled) or fact[key].strip() != u"":
                continue
        
            # Update the value in that field
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
    
    class FieldUpdaterTest(unittest.TestCase):
        def testAutoBlanking(self):
            self.assertEquals(self.updatefact(u"", { "reading" : "blather", "meaning" : "junk", "color" : "yes!" }),
                              { "reading" : "", "meaning" : "", "color" : "" })
        
        def testAutoBlankingAudioMeasureWord(self):
            # TODO: test behaviour for audio and measure word, once we know what it should be
            pass
        
        def testFullUpdate(self):
            self.assertEquals(
                self.updatefact(u"书", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                    colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True,
                    tonedisplay = "tonified", meaningnumbering = "circledChinese", meaningseperator = "lines", prefersimptrad = "simp",
                    audiogeneration = True, audioextensions = [".mp3"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"]), {
                        "reading" : u'<span style="color:#ff0000">shū</span>',
                        "meaning" : u'㊀ book<br />㊁ letter<br />㊂ same as <span style="color:#ff0000">\u4e66</span><span style="color:#ff0000">\u7ecf</span> Book of History',
                        "mw" : u'本 - <span style="color:#00aa00">běn</span>, 册 - <span style="color:#0000ff">cè</span>, 部 - <span style="color:#0000ff">bù</span>, 丛 - <span style="color:#ffaa00">cóng</span>',
                        "audio" : u"[sound:" + os.path.join("Test", "shu1.mp3") + "]",
                        "color" : u'<span style="color:#ff0000">书</span>'
                      })
        
        def testDontOverwriteFields(self):
            self.assertEquals(
                self.updatefact(u"书", { "reading" : "a", "meaning" : "b", "mw" : "c", "audio" : "d", "color" : "e" },
                    colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True,
                    tonedisplay = "tonified", meaningnumbering = "circledChinese", meaningseperator = "lines", prefersimptrad = "simp",
                    audiogeneration = True, audioextensions = [".mp3"], tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"]), {
                        "reading" : "a", "meaning" : "b", "mw" : "c", "audio" : "d", "color" : "e"
                      })
        
        def testUpdateExpressionItself(self):
            self.assertEquals(
                self.updatefact(u"啤酒", { "expression" : "" },
                    colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False,
                    detectmeasurewords = False, audiogeneration = False), { "expression" : u"啤酒" })
        
        def testUpdateReadingOnly(self):
            self.assertEquals(
                self.updatefact(u"啤酒", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                    colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False,
                    detectmeasurewords = False, audiogeneration = False, tonedisplay = "numeric"), {
                        "reading" : u'pi2 jiu3', "meaning" : "", "mw" : "", "audio" : "", "color" : ""
                      })
        
        def testUpdateReadingAndMeaning(self):
            self.assertEquals(
                self.updatefact(u"㝵", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                    colorizedpinyingeneration = True, colorizedcharactergeneration = False, meaninggeneration = True, detectmeasurewords = False,
                    tonedisplay = "numeric", meaningnumbering = "arabicParens", meaningseperator = "commas", prefersimptrad = "trad",
                    audiogeneration = False, tonecolors = [u"#ff0000", u"#ffaa00", u"#00aa00", u"#0000ff", u"#545454"]), {
                        "reading" : u'<span style="color:#ffaa00">de2</span>',
                        "meaning" : u'(1) to obtain, (2) archaic variant of 得 - <span style="color:#ffaa00">de2</span>, (3) component in 礙 - <span style="color:#0000ff">ai4</span> and 鍀 - <span style="color:#ffaa00">de2</span>',
                        "mw" : "", "audio" : "", "color" : ""
                      })
        
        def testUpdateReadingAndMeasureWord(self):
            self.assertEquals(
                self.updatefact(u"丈夫", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                    colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = True,
                    tonedisplay = "numeric", prefersimptrad = "trad", audiogeneration = False), {
                        "reading" : u'zhang4 fu', "meaning" : u'',
                        "mw" : u"個 - ge4", "audio" : "", "color" : ""
                      })
        
        def testUpdateReadingAndAudio(self):
            self.assertEquals(
                self.updatefact(u"三七開", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                    colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = False,
                    tonedisplay = "tonified", audiogeneration = True, audioextensions = [".mp3", ".ogg"]), {
                        "reading" : u'sān qī kāi', "meaning" : u'', "mw" : "",
                        "audio" : u"[sound:" + os.path.join("Test", "san1.mp3") + "]" +
                                  u"[sound:" + os.path.join("Test", "qi1.ogg") + "]" +
                                  u"[sound:" + os.path.join("Test", "location/Kai1.mp3") + "]",
                        "color" : ""
                      })
        
        def testUpdateReadingAndColoredHanzi(self):
            self.assertEquals(
                self.updatefact(u"三峽水库", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                    colorizedpinyingeneration = False, colorizedcharactergeneration = True, meaninggeneration = False, detectmeasurewords = False,
                    tonedisplay = "numeric", audiogeneration = False, tonecolors = [u"#111111", u"#222222", u"#333333", u"#444444", u"#555555"]), {
                        "reading" : u'san1 xia2 shui3 ku4', "meaning" : u'', "mw" : "", "audio" : "",
                        "color" : u'<span style="color:#111111">三</span><span style="color:#222222">峽</span><span style="color:#333333">水</span><span style="color:#444444">库</span>'
                      })
        
        def testNotifiedUponAudioGenerationWithNoPacks(self):
            infos, fact = self.updatefactwithinfos(u"三月", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                                mediapacks = [],
                                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = False,
                                tonedisplay = "numeric", audiogeneration = True)
            
            self.assertEquals(fact, { "reading" : u'san1 yue4', "meaning" : u'', "mw" : "", "audio" : "", "color" : "" })
            self.assertEquals(len(infos), 1)
            self.assertTrue("missing" in infos[0])
        
        def testFallBackOnGoogleForPhrase(self):
            self.assertEquals(
                self.updatefact(u"㝵㝵㝵㝵㝵", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                    fallbackongoogletranslate = True,
                    colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = True, detectmeasurewords = False,
                    tonedisplay = "numeric", audiogeneration = False), {
                        "reading" : u'de2 de2 de2 de2 de2',
                        "meaning" : u'㝵㝵㝵㝵㝵<br /><span style="color:gray"><small>[Google Translate]</small></span>',
                        "mw" : "", "audio" : "", "color" : ""
                      })
        
        # Test helpers
        def updatefact(self, *args, **kwargs):
            infos, fact = self.updatefactwithinfos(*args, **kwargs)
            return fact
        
        def updatefactwithinfos(self, expression, fact, mediapacks = None, **kwargs):
            notifier = MockNotifier()
            
            if mediapacks == None:
                mediapacks = [media.MediaPack("Test", { "shu1.mp3" : "shu1.mp3", "san1.mp3" : "san1.mp3", "qi1.ogg" : "qi1.ogg", "Kai1.mp3" : "location/Kai1.mp3" })]
            mediamanager = MockMediaManager(mediapacks)
            
            factclone = copy.deepcopy(fact)
            FieldUpdater(notifier, mediamanager, config.Config(kwargs), englishdict).updatefact(factclone, expression)
            
            return notifier.infos, factclone
    
    unittest.main()
