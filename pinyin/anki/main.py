#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pinyin.dictionaryonline
import pinyin.dictionary
from pinyin.logger import log
import pinyin.media

import hooks
import notifier
import updater
import utils

import statsandgraphs
import shortcutkeys


class PinyinToolkit(object):
    def __init__(self, mw, config):
        log.info("Pinyin Toolkit is initializing")
        
        # Test internet connectivity by performing a gTrans call.
        # If this call fails then translations are disabled until Anki is restarted.
        # This prevents a several second delay from occuring when changing a field with no internet
        if (config.fallbackongoogletranslate):
            config.fallbackongoogletranslate = pinyin.dictionaryonline.gCheck(config.dictlanguage)
            log.info("Google Translate has tested internet access and reports status %s", config.fallbackongoogletranslate)
        
        # Store the configuration and mw
        self.mw = mw
        self.config = config
        
        # Build notifier
        self.notifier = notifier.AnkiNotifier()
        
        # Build the updater
        dictionary = pinyin.dictionary.PinyinDictionary.load(config.dictlanguage, needmeanings=utils.needmeanings(config))
        mediapacks = self.discovermedia()
        self.updater = updater.FieldUpdater(self.config, dictionary, mediapacks, self.notifier)
        
        # Finally, build the hooks.  Make sure you store a reference to these, because otherwise they
        # get garbage collected, causing garbage collection of the actions they contain
        self.hooks = [hookbuilder(self.mw, self.notifier, self.config, self.updater) for hookbuilder in [hooks.FocusHook, hooks.SampleSoundsHook, hooks.MissingInformationHook]]
    
    def installhooks(self):
        # Install all hooks
        for hook in self.hooks:
            hook.install()
    
        # Tell Anki about the plugin
        self.mw.registerPlugin("Mandarin Chinese Pinyin Toolkit", 4)
    
    def discovermedia(self):
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
        
        # Finally, list the packs
        return pinyin.media.MediaPack.discover(mediadircontents, self.mw.deck.s.all("select originalPath, filename from media"))
