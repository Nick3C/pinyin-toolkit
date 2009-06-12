#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore

import anki.utils

import pinyin.forms.preferences
import pinyin.forms.preferencescontroller
from pinyin.logger import log
import pinyin.media
import pinyin.transformations
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
        
        # Install hook into focus event of Anki: we regenerate the model information when
        # the cursor moves from the Expression field to another field
        log.info("Installing focus hook")
        
        try:
            # On versions of Anki that still had Chinese support baked in, remove the
            # provided hook from this event before we replace it with our own:
            from anki.features.chinese import onFocusLost as oldHook
            removeHook('fact.focusLost', oldHook)
        except ImportError:
            pass
        
        # Unconditionally add our new hook to Anki
        addHook('fact.focusLost', self.onFocusLost)

# Shrunk version of color shortcut plugin merged with Pinyin Toolkit to give that functionality without the seperate download.
# Original version by Damien Elmes <anki@ichi2.net>
class ColorShortcutKeysHook(Hook):
    def setColor(self, editor, i, sandhify):
        log.info("Got color change event for color %d, sandhify %s", i, sandhify)
        
        color = (self.config.tonecolors + self.config.extraquickaccesscolors)[i - 1]
        if sandhify:
            color = pinyin.transformations.sandhifycolor(color)
        
        focusededit = editor.focusedEdit()
        
        cursor = focusededit.textCursor()
        focusededit.setTextColor(QtGui.QColor(color))
        cursor.clearSelection()
        focusededit.setTextCursor(cursor)
    
    def setupShortcuts(self, editor):
        # Loop through the 8 F[x] keys, setting each one up
        # Note: Ctrl-F9 is the HTML editor. Don't do this as it causes a conflict
        log.info("Setting up shortcut buttons on fact editor")
        for i in range(1, 9):
            for sandhify in [True, False]:
                # Build the invisible button used to gather shortcut events
                button = QtGui.QPushButton()
                button.setText(str(i) + (sandhify and "S" or ""))
                button.setShortcut((sandhify and "Shift+" or "") + "Ctrl+F" + str(i))
                button.setFocusPolicy(QtCore.Qt.NoFocus)
                button.setFixedSize(0, 0)
            
                # Add the button to the icons box on the fact editor
                editor.iconsBox.addWidget(button)
            
                # Connect button to event handler: note hacks to deal with closure scoping
                self.mw.connect(button, QtCore.SIGNAL("clicked()"), lambda i=i, sandhify=sandhify: self.setColor(editor, i, sandhify))
            
                # Possible alternative approach?
                # QtGui.QShortcut(QtGui.QKeySequence("Ctrl+F" + str(i)), self.mw, lambda i=i: self.setColor(editor, i))
    
    def install(self):
        from anki.hooks import wrap
        import ankiqt.ui.facteditor
        
        log.info("Installing color shortcut keys hook")
        ankiqt.ui.facteditor.FactEditor.setupFields = wrap(ankiqt.ui.facteditor.FactEditor.setupFields, self.setupShortcuts, "after")
        self.setupShortcuts(self.mw.editor)

class MenuHook(Hook):
    pinyinToolkitMenu = None
    
    def install(self):
        # Install menu item
        log.info("Installing a menu hook (%s)", type(self))
        
        # Build and install the top level menu if it doesn't already exist
        if MenuHook.pinyinToolkitMenu is None:
            MenuHook.pinyinToolkitMenu = QtGui.QMenu("Pinyin Toolkit", self.mw.mainWin.menuTools)
            self.mw.mainWin.menuTools.addMenu(MenuHook.pinyinToolkitMenu)
        
        # Store the action on the class.  Storing a reference to it is necessary to avoid it getting garbage collected.
        self.action = QtGui.QAction(self.__class__.menutext, self.mw)
        self.action.setStatusTip(self.__class__.menutooltip)
        self.action.setEnabled(True)
        
        # HACK ALERT: must use lambda here, or the signal never gets raised! I think this is due to garbage collection...
        self.mw.connect(self.action, QtCore.SIGNAL('triggered()'), lambda: self.triggered())
        MenuHook.pinyinToolkitMenu.addAction(self.action)

class HelpHook(Hook):
    def install(self):
        # Store the action on the class.  Storing a reference to it is necessary to avoid it getting garbage collected.
        self.action = QtGui.QAction("Pinyin Toolkit", self.mw)
        self.action.setStatusTip("Help for the Pinyin Toolkit available at our website")
        self.action.setEnabled(True)
        
        helpUrl = QtCore.QUrl(u"http://batterseapower.github.com/pinyin-toolkit/")
        self.mw.connect(self.action, QtCore.SIGNAL('triggered()'), lambda: QtGui.QDesktopServices.openUrl(helpUrl))
        self.mw.mainWin.menuHelp.addAction(self.action)

class PreferencesHook(MenuHook):
    menutext = "Preferences"
    menutooltip = "Configure the Pinyin Toolkit"
    
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
    menutext = 'Fill missing card data'
    menutooltip = 'Update all the cards in the deck with any missing information the Pinyin Toolkit can provide.'
    
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
