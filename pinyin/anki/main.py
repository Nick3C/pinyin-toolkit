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

hookbuilders = hooks.hookbuilders + [
    statsandgraphs.HanziGraphHook
  ]

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
        
        # Build the updaters
        updaters = {
            'expression' : pinyin.updater.FieldUpdaterFromExpression(thenotifier, themediamanager, config),
            'reading'    : pinyin.updater.FieldUpdaterFromReading(config)
          }
        
        # Finally, build the hooks.  Make sure you store a reference to these, because otherwise they
        # get garbage collected, causing garbage collection of the actions they contain
        self.hooks = [hookbuilder(self.mw, thenotifier, themediamanager, config, updaters) for hookbuilder in hookbuilders]
    
    def installhooks(self):
        # Install all hooks
        for hook in self.hooks:
            hook.install()
    
        # Tell Anki about the plugin
        self.mw.registerPlugin("Mandarin Chinese Pinyin Toolkit", 4)
        self.registerStandardModels()
    
    def registerStandardModels(self):
        # This code was added at the request of Damien: one of the changes in the next
        # Anki version will be to make language-specific toolkits into plugins.
        #
        # The code sets up a 'template' model for users. We probably want to customize
        # this eventually, but for now it's a duplicate of the old code from Anki.
        
        import anki.stdmodels
        from anki.models import Model, CardModel, FieldModel

        # Mandarin
        ##########################################################################

        def MandarinModel():
           m = Model(_("Mandarin"))
           f = FieldModel(u'Expression')
           f.quizFontSize = 72
           m.addFieldModel(f)
           m.addFieldModel(FieldModel(u'Meaning', False, False))
           m.addFieldModel(FieldModel(u'Reading', False, False))
           m.addCardModel(CardModel(u"Recognition",
                                    u"%(Expression)s",
                                    u"%(Reading)s<br>%(Meaning)s"))
           m.addCardModel(CardModel(u"Recall",
                                    u"%(Meaning)s",
                                    u"%(Expression)s<br>%(Reading)s",
                                    active=False))
           m.tags = u"Mandarin"
           return m

        anki.stdmodels.models['Mandarin'] = MandarinModel
