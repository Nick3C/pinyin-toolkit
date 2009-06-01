#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore

import anki.utils

import pinyin.utils
import pinyin.media

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
        # Have we just moved off the expression field in a Mandarin model?
        expressionField = utils.chooseField(self.config.candidateFieldNamesByKey['expression'], fact)
        if field.name != expressionField or not(anki.utils.findTag(self.config.modelTag, fact.model.tags)):
            return
        if field.value != "": # don't do if blank, causes lots of problems
            # Update the card, ignoring any errors
            utils.suppressexceptions(lambda: updatefact(fact, field.value))
    
    def install(self):
        from anki.hooks import addHook, removeHook
        from anki.features.chinese import onFocusLost as oldHook

        # Install hook into focus event of Anki: we regenerate the model information when
        # the cursor moves from the Expression field to another field
        removeHook('fact.focusLost', oldHook)
        addHook('fact.focusLost', self.onFocusLost)


# DEBUG - I think these should really be moved to advanced. They aren't going to be run very often and will get in the way. (let's not make Damien complain :)

class SampleSoundsHook(Hook):
    def downloadAndInstallSounds(self):
        # Download ZIP, using cache if necessary
        the_media = pinyin.media.MediaDownloader().download(mandarinsoundsurl,
                                                            lambda: self.notifier.info("Downloading the sounds - this might take a while!"))
    
        # Install each file from the ZIP into Anki
        the_media.extractand(self.mw.deck.addMedia)
    
        # Tell the user we are done
        exampleAudioField = self.config.candidateFieldNamesByKey['audio'][0]
        self.notifier.info("Finished installing Mandarin sounds! These sound files will be used automatically as long as you have "
                           + " the: <b>" + exampleAudioField + "</b> field in your deck, and the text: <b>%(" + exampleAudioField + ")s</b> in your card template")

    def install(self):
        # Install menu item that will allow downloading of the sounds
        action = QtGui.QAction('Download Mandarin text-to-speech Audio Files', self.mw)
        action.setStatusTip('Download and install a sample set of Mandarin audio files into this deck. This will enable automatic text-to-speech.')
        action.setEnabled(True)

        self.mw.connect(action, QtCore.SIGNAL('triggered()'), self.downloadAndInstallSounds)
        self.mw.mainWin.menuTools.addAction(action)


class MissingInformationHook(Hook):
    def suitableCards(self, deck):
        for model in deck.models:
            if anki.utils.findTag(modelTag, model.tags):
                card_model = deck.s.scalar('select id from cardmodels where modelId = %s' % model.id)
                for card in deck.s.query(anki.cards.Card).filter('cardModelId = %s' % card_model):
                    yield card

    def fillMissingInformation(self):
        for card in self.suitableCards(self.mw.deck):
            expressionField = utils.chooseField(self.config.candidateFieldNamesByKey['expression'], card.fact)
            self.updater.updatefact(self.notifier, card.fact, card.fact[expressionField])
    
        # DEBUG consider future feature to add missing measure words cards after doing so (not now)
        self.notifier.info("All missing information has been successfully added to your deck.")

    def install(self):
        # Install menu item that will allow filling of missing information
        action = QtGui.QAction('Fill all missing card data using Pinyin Toolkit', self.mw)
        action.setStatusTip('Update all the cards in the deck with any missing information the Pinyin Toolkit can provide.')
        action.setEnabled(True)

        self.mw.connect(action, QtCore.SIGNAL('triggered()'), self.fillMissingInformation)
        self.mw.mainWin.menuTools.addAction(action)
