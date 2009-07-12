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
    def __init__(self, mw, notifier, mediamanager, config, updaters):
        self.mw = mw
        self.notifier = notifier
        self.mediamanager = mediamanager
        self.config = config
        self.updaters = updaters

class FocusHook(Hook):
    def onFocusLost(self, fact, field):
        log.info("User moved focus from the field %s", field.name)
        
        # Are we not in a Mandarin model?
        if not(anki.utils.findTag(self.config.modelTag, fact.model.tags)):
            return
        
        # Need a fact proxy because the updater works on dictionary-like objects
        factproxy = utils.AnkiFactProxy(self.config.candidateFieldNamesByKey, fact)
        
        # Find which kind of field we have just moved off
        updater = None
        for key, fieldname in factproxy.fieldnames.items():
            if field.name == fieldname:
                updater = self.updaters.get(key)
                break

        # Update the card, ignoring any errors
        if updater:
            pinyin.utils.suppressexceptions(lambda: updater.updatefact(factproxy, field.value))
    
    def install(self):
        from anki.hooks import addHook, removeHook
        
        # Install hook into focus event of Anki: we regenerate the model information when
        # the cursor moves from the Expression/Reading/whatever field to another field
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
        log.info("Setting up shortcut keys on fact editor")
        for i in range(1, 9):
            for sandhify in [True, False]:
                keysequence = (sandhify and ColorShortcutKeysHook.sandhiModifier + "+" or "") + ColorShortcutKeysHook.shortcutKeyFor(i)
                QtGui.QShortcut(QtGui.QKeySequence(keysequence), editor.widget,
                                lambda i=i, sandhify=sandhify: self.setColor(editor, i, sandhify))
    
    def install(self):
        from anki.hooks import wrap
        import ankiqt.ui.facteditor
        
        log.info("Installing color shortcut keys hook")
        ankiqt.ui.facteditor.FactEditor.setupFields = wrap(ankiqt.ui.facteditor.FactEditor.setupFields, self.setupShortcuts, "after")
        self.setupShortcuts(self.mw.editor)
    
    
    sandhiModifier = "Shift"
    
    @classmethod
    def shortcutKeyFor(cls, i):
        if pinyin.utils.isosx():
            # Alt maps to the Windows key on my keyboard, NOT the Alt key.
            # NB: Ctrl maps to Option on OS X, and Option+Fx conflicts with
            # some special meanings given to those keys on Mac laptops.
            return "Alt+" + str(i)
        else:
            return "Ctrl+F" + str(i)

class HelpHook(Hook):
    def install(self):
        # Store the action on the class.  Storing a reference to it is necessary to avoid it getting garbage collected.
        self.action = QtGui.QAction("Pinyin Toolkit", self.mw)
        self.action.setStatusTip("Help for the Pinyin Toolkit available at our website")
        self.action.setEnabled(True)
        
        helpUrl = QtCore.QUrl(u"http://batterseapower.github.com/pinyin-toolkit/")
        self.mw.connect(self.action, QtCore.SIGNAL('triggered()'), lambda: QtGui.QDesktopServices.openUrl(helpUrl))
        self.mw.mainWin.menuHelp.addAction(self.action)

class PreferencesHook(Hook):
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
    
    def install(self):
        # Store the action on the class.  Storing a reference to it is necessary to avoid it getting garbage collected.
        self.action = QtGui.QAction("Pinyin Tool&kit Preferences", self.mw)
        self.action.setStatusTip("Configure the Pinyin Toolkit")
        self.action.setMenuRole(QtGui.QAction.PreferencesRole)
        self.action.setEnabled(True)
        
        self.mw.connect(self.action, QtCore.SIGNAL('triggered()'), lambda: self.triggered())
        self.mw.mainWin.menu_Settings.addAction(self.action)

class ToolMenuHook(Hook):
    pinyinToolkitMenu = None
    
    def install(self):
        # Install menu item
        log.info("Installing a menu hook (%s)", type(self))
        
        # Build and install the top level menu if it doesn't already exist
        if ToolMenuHook.pinyinToolkitMenu is None:
            ToolMenuHook.pinyinToolkitMenu = QtGui.QMenu("Pinyin Toolkit", self.mw.mainWin.menuTools)
            self.mw.mainWin.menuTools.addMenu(ToolMenuHook.pinyinToolkitMenu)
        
        # Store the action on the class.  Storing a reference to it is necessary to avoid it getting garbage collected.
        self.action = QtGui.QAction(self.__class__.menutext, self.mw)
        self.action.setStatusTip(self.__class__.menutooltip)
        self.action.setEnabled(True)
        
        # HACK ALERT: must use lambda here, or the signal never gets raised! I think this is due to garbage collection...
        # We try and make sure that we don't run the action if there is no deck presently, to at least suppress some errors
        # in situations where the users select the menu items (this is possible on e.g. OS X). It would be better to disable
        # the menu items entirely in these situations, but there is no suitable hook for that presently.
        self.mw.connect(self.action, QtCore.SIGNAL('triggered()'), lambda: self.mw.deck is not None and self.triggered())
        ToolMenuHook.pinyinToolkitMenu.addAction(self.action)

class MassFillHook(ToolMenuHook):
    def triggered(self):
        field = self.__class__.field
        log.info("User triggered missing information fill for %s" % field)
        
        for fact in utils.suitableFacts(self.config.modelTag, self.mw.deck):
            # Need a fact proxy because the updater works on dictionary-like objects
            factproxy = utils.AnkiFactProxy(self.config.candidateFieldNamesByKey, fact)
            if field not in factproxy:
                continue
            
            getattr(self.updaters[field], self.__class__.updatehow)(factproxy, factproxy[field])
            
            # NB: very important to mark the fact as modified (see #105) because otherwise
            # the HTML etc won't be regenerated by Anki, so users may not e.g. get working
            # sounds that have just been filled in by the updater.
            fact.setModified(textChanged=True)
        
        # For good measure, mark the deck as modified as well (see #105)
        self.mw.deck.setModified()
    
        # DEBUG consider future feature to add missing measure words cards after doing so (not now)
        self.notifier.info(self.__class__.notification)

class MissingInformationHook(MassFillHook):
    menutext = 'Fill missing card data'
    menutooltip = 'Update all the cards in the deck with any missing information the Pinyin Toolkit can provide.'
    
    field = "expression"
    updatehow = "updatefact"
    
    notification = "All missing information has been successfully added to your deck."

class ReformatReadingsHook(MassFillHook):
    menutext = 'Reformat readings'
    menutooltip = 'Update all the readings in your deck with colorisation and tones according to your preferences.'
    
    field = "reading"
    updatehow = "updatefactalways"
    
    notification = "All readings have been successfully reformatted."

# NB: this must go at the end of the file, after all the definitions are in scope
hookbuilders = [
    # Focus hook
    FocusHook,
    # Keybord hooks
    ColorShortcutKeysHook,
    # Menu hooks
    HelpHook,
    PreferencesHook,
    MissingInformationHook,
    ReformatReadingsHook
  ]