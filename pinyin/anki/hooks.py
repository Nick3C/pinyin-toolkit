#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore

import anki.utils

from pinyin.logger import log
import pinyin.media
import pinyin.utils

import updater
import utils


class Hook(object):
    def __init__(self, mw, notifier, config, updater):
        self.mw = mw
        self.notifier = notifier
        self.config = config
        self.updater = updater

class FocusHook(Hook):
    def onFocusLost(self, fact, field):
        log.info("User moved focus from the field %s", field)
        
        # Have we just moved off the expression field in a Mandarin model?
        expressionField = utils.chooseField(self.config.candidateFieldNamesByKey['expression'], fact)
        if field.name != expressionField or not(anki.utils.findTag(self.config.modelTag, fact.model.tags)):
            return

        # Update the card, ignoring any errors
        pinyin.utils.suppressexceptions(lambda: self.updater.updatefact(self.notifier, fact, field.value))
    
    def install(self):
        from anki.hooks import addHook, removeHook
        from anki.features.chinese import onFocusLost as oldHook

        # Install hook into focus event of Anki: we regenerate the model information when
        # the cursor moves from the Expression field to another field
        log.info("Installing focus hook")
        removeHook('fact.focusLost', oldHook)
        addHook('fact.focusLost', self.onFocusLost)


# DEBUG - I think these should really be moved to advanced. They aren't going to be run very often and will get in the way. (let's not make Damien complain :)

class MenuHook(Hook):
    def __init__(self, text, tooltip, *args, **kwargs):
        Hook.__init__(self, *args, **kwargs)
        
        # Store the action on the class.  Storing a reference to it is necessary to avoid it getting garbage collected.
        self.action = QtGui.QAction(text, self.mw)
        self.action.setStatusTip(tooltip)
        self.action.setEnabled(True)

class SampleSoundsHook(MenuHook):
    def __init__(self, *args, **kwargs):
        MenuHook.__init__(self,
                          'Download Mandarin text-to-speech Audio Files',
                          'Download and install a sample set of Mandarin audio files into this deck. This will enable automatic text-to-speech.',
                           *args,
                           **kwargs)

    def downloadAndInstallSounds(self):
        log.info("User triggered sound download")
        
        # Download ZIP, using cache if necessary
        the_media = pinyin.media.MediaDownloader().download(self.config.mandarinsoundsurl,
                                                            lambda: self.notifier.info("Downloading the sounds - this might take a while!"))
    
        # Install each file from the ZIP into Anki
        the_media.extractand(self.mw.deck.addMedia)
    
        # Tell the user we are done
        exampleAudioField = self.config.candidateFieldNamesByKey['audio'][0]
        self.notifier.info("Finished installing Mandarin sounds! These sound files will be used automatically as long as you have "
                           + " the: <b>" + exampleAudioField + "</b> field in your deck, and the text: <b>%(" + exampleAudioField + ")s</b> in your card template")

    def install(self):
        # Install menu item that will allow downloading of the sounds
        log.info("Installing sample sounds hook")
        # HACK ALERT: must use lambda here, or the signal never gets raised! I think this is due to garbage collection...
        self.mw.connect(self.action, QtCore.SIGNAL('triggered()'), lambda: self.downloadAndInstallSounds())
        self.mw.mainWin.menuTools.addAction(self.action)


class MissingInformationHook(MenuHook):
    def __init__(self, *args, **kwargs):
        MenuHook.__init__(self,
                          'Fill all missing card data using Pinyin Toolkit',
                          'Update all the cards in the deck with any missing information the Pinyin Toolkit can provide.',
                           *args,
                           **kwargs)
    
    def suitableCards(self, deck):
        for model in deck.models:
            if anki.utils.findTag(self.config.modelTag, model.tags):
                card_model = deck.s.scalar('select id from cardmodels where modelId = %s' % model.id)
                for card in deck.s.query(anki.cards.Card).filter('cardModelId = %s' % card_model):
                    yield card

    def fillMissingInformation(self):
        log.info("User triggered missing information fill")
        
        for card in self.suitableCards(self.mw.deck):
            expressionField = utils.chooseField(self.config.candidateFieldNamesByKey['expression'], card.fact)
            self.updater.updatefact(self.notifier, card.fact, card.fact[expressionField])
    
        # DEBUG consider future feature to add missing measure words cards after doing so (not now)
        self.notifier.info("All missing information has been successfully added to your deck.")

    def install(self):
        # Install menu item that will allow filling of missing information
        log.info("Installing missing information hook")
        # HACK ALERT: must use lambda here, or the signal never gets raised! I think this is due to garbage collection...
        self.mw.connect(self.action, QtCore.SIGNAL('triggered()'), lambda: self.fillMissingInformation())
        self.mw.mainWin.menuTools.addAction(self.action)
