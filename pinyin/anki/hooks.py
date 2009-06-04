#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore

import anki.utils

import pinyin.forms.preferences
import pinyin.forms.preferencescontroller
from pinyin.logger import log
import pinyin.media
import pinyin.utils

import utils


class Hook(object):
    def __init__(self, mw, notifier, mediamanager, config, updater):
        self.mw = mw
        self.notifier = notifier
        self.mediamanager = mediamanager
        self.config = config
        self.updater = updater

class FocusHook(Hook):
    def onFocusLost(self, fact, field):
        log.info("User moved focus from the field %s", field.name)
        
        # Need a fact proxy because the updater works on dictionary-like objects
        factproxy = utils.AnkiFactProxy(self.config.candidateFieldNamesByKey, fact)
        
        # Have we just moved off the expression field in a Mandarin model?
        if field.name != factproxy.fieldnames.get("expression") or not(anki.utils.findTag(self.config.modelTag, fact.model.tags)):
            return

        # Update the card, ignoring any errors
        pinyin.utils.suppressexceptions(lambda: self.updater.updatefact(factproxy, field.value))
    
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
    pinyinToolkitMenu = None
    
    def __init__(self, text, tooltip, *args, **kwargs):
        Hook.__init__(self, *args, **kwargs)
        
        # Store the action on the class.  Storing a reference to it is necessary to avoid it getting garbage collected.
        self.action = QtGui.QAction(text, self.mw)
        self.action.setStatusTip(tooltip)
        self.action.setEnabled(True)
    
    def install(self):
        # Install menu item
        log.info("Installing a menu hook (%s)", type(self))
        
        # Build and install the top level menu if it doesn't already exist
        if MenuHook.pinyinToolkitMenu is None:
            MenuHook.pinyinToolkitMenu = QtGui.QMenu("Pinyin Toolkit", self.mw.mainWin.menuTools)
            self.mw.mainWin.menuTools.addMenu(MenuHook.pinyinToolkitMenu)
        
        # HACK ALERT: must use lambda here, or the signal never gets raised! I think this is due to garbage collection...
        self.mw.connect(self.action, QtCore.SIGNAL('triggered()'), lambda: self.triggered())
        MenuHook.pinyinToolkitMenu.addAction(self.action)

class PreferencesHook(MenuHook):
    def __init__(self, *args, **kwargs):
        MenuHook.__init__(self,
                          "Preferences",
                          "Configure the Pinyin Toolkit",
                          *args,
                          **kwargs)
    
    def triggered(self):
        log.info("User opened preferences dialog")
        
        # Instantiate and show the preferences dialog modally
        preferences = pinyin.forms.preferences.Preferences(self.mw)
        controller = pinyin.forms.preferencescontroller.PreferencesController(preferences, self.notifier, self.mediamanager, self.config)
        result = preferences.exec_()
        
        # We only need to change the configuration if the user accepted the dialog
        if result == QtGui.QDialog.Accepted:
            # Update by the simple method of replacing the settings dictionaries: better make sure that no
            # other part of the code has cached parts of the configuration
            self.config.settings = controller.model.settings
            
            # Ensure this is saved in Anki's configuration
            utils.persistconfig(self.mw, self.config)
        
class MissingInformationHook(MenuHook):
    def __init__(self, *args, **kwargs):
        MenuHook.__init__(self,
                          'Fill missing card data',
                          'Update all the cards in the deck with any missing information the Pinyin Toolkit can provide.',
                           *args,
                           **kwargs)
    
    def suitableCards(self, deck):
        for model in deck.models:
            if anki.utils.findTag(self.config.modelTag, model.tags):
                card_model = deck.s.scalar('select id from cardmodels where modelId = %s' % model.id)
                for card in deck.s.query(anki.cards.Card).filter('cardModelId = %s' % card_model):
                    yield card

    def triggered(self):
        log.info("User triggered missing information fill")
        
        for card in self.suitableCards(self.mw.deck):
            # Need a fact proxy because the updater works on dictionary-like objects
            factproxy = utils.AnkiFactProxy(self.config.candidateFieldNamesByKey, card.fact)
            self.updater.updatefact(factproxy, factproxy["expression"])
    
        # DEBUG consider future feature to add missing measure words cards after doing so (not now)
        self.notifier.info("All missing information has been successfully added to your deck.")
