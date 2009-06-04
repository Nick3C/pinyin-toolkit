#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pinyin.config
import pinyin.dictionaryonline
import pinyin.dictionary
from pinyin.logger import log
import pinyin.updater

import hooks
import mediamanager
import notifier
import utils

import statsandgraphs
import shortcutkeys


class PinyinToolkit(object):
    def __init__(self, mw):
        log.info("Pinyin Toolkit is initializing")
        
        # Try and load the settings from the Anki config database
        settings = mw.config.get("pinyintoolkit")
        if settings is None:
            # Initialize the configuration with default settings
            config = pinyin.config.Config()
            utils.persistconfig(mw, config)
        else:
            # Initialize the configuration with the stored settings
            config = pinyin.config.Config(settings)
        
        # Store the main window
        self.mw = mw
        
        # Build objects we use to interface with Anki
        thenotifier = notifier.AnkiNotifier()
        themediamanager = mediamanager.AnkiMediaManager(self.mw)
        
        # Build the updater
        updater = pinyin.updater.FieldUpdater(thenotifier, themediamanager, config)
        
        # Finally, build the hooks.  Make sure you store a reference to these, because otherwise they
        # get garbage collected, causing garbage collection of the actions they contain
        self.hooks = [hookbuilder(self.mw, thenotifier, themediamanager, config, updater) for hookbuilder in [hooks.PreferencesHook, hooks.FocusHook, hooks.MissingInformationHook]]
    
    def installhooks(self):
        # Install all hooks
        for hook in self.hooks:
            hook.install()
    
        # Tell Anki about the plugin
        self.mw.registerPlugin("Mandarin Chinese Pinyin Toolkit", 4)
