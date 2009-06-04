#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtCore import QVariant
from PyQt4.QtGui import QColor, QIcon, QPalette

import pinyin.config
from pinyin.languages import languages
import pinyin.utils

class PreferencesController(object):
    def __init__(self, view, initialconfig):
        # Clone the configuration so we can change it at will
        self.model = pinyin.config.Config(initialconfig.settings)
    
        # Save the view (typically a Preferences instance) for later reference
        self.view = view
        
        # Set up the controls - one time only
        self.mappings = []
        self.setUpText()
        
        # Reflect the initial setting values into the controls
        self.updateView()
    
    #
    # Setup
    #
    
    def setUpText(self):
        # The Hanzi and Pinyin panel
        def setUpHanziPinyin():
            self.registerRadioMapping("tonedisplay", {
                self.view.controls.numericPinyinTonesRadio : "numeric",
                self.view.controls.tonifiedPinyinTonesRadio : "tonified"
              })
            
            self.registerRadioMapping("prefersimptrad", {
                self.view.controls.simplifiedHanziRadio : "simp",
                self.view.controls.traditionalHanziRadio : "trad"
              })
        
        # The Meanings panel
        def setUpMeanings():
            # Add languages to the combo box lexically sorted by support level, then by friendly name
            lastsupportlevel = None
            for supportlevel, langcode, countrycode, name in sorted(languages, lambda x, y: cmp((y[0], x[3]), (x[0], y[3]))):
                # Add a seperator if we have moved to a new support level
                if lastsupportlevel != None and supportlevel != lastsupportlevel:
                    self.addComboSeparator(self.view.controls.languageCombo)
                lastsupportlevel = supportlevel
            
                # Decide on the icon to use, if any
                if countrycode:
                    icon = ":/flags/%s.png" % countrycode
                else:
                    icon = None
            
                # Set the langcode as the user data for the combo item - this
                # will be picked up by the ComboMapping stuff
                self.addComboItem(self.view.controls.languageCombo, icon, name, langcode)
            
            self.registerCheckMapping("detectmeasurewords", self.view.controls.seperateMeasureWordCheck)
            
            self.registerComboMapping("dictlanguage", self.view.controls.languageCombo)
            
            self.registerCheckMapping("fallbackongoogletranslate", self.view.controls.googleTranslateCheck)
            
            self.registerRadioMapping("meaningnumbering", {
                self.view.controls.circledChineseNumberingRadio : "circledChinese",
                self.view.controls.circledArabicNumberingRadio : "circledArabic",
                self.view.controls.plainNumberingRadio : "arabicParens",
                self.view.controls.noNumberingRadio : "none",
              })
            
            self.registerRadioMapping("meaningseperator", {
                self.view.controls.linesSeperatorRadio : "lines",
                self.view.controls.commasSeperatorRadio : "commas",
                self.view.controls.customSeperatorRadio : "custom"
              })
            
            self.registerTextMapping("custommeaningseperator", self.view.controls.customSeperatorLineEdit)
        
        # The Tone Colors panel
        def setUpToneColors():
            self.registerCheckMapping("colorizedpinyingeneration", self.view.controls.colorizeCheck)
            
            for tone in range(1, 6):
                self.registerColorChooserMapping("tone%dcolor" % tone, getattr(self.view.controls, "tone%dButton" % tone))
        
        setUpHanziPinyin()
        setUpMeanings()
        setUpToneColors()
    
    def addComboItem(self, combo, icon, name, data):
        if icon:
            combo.addItem(QIcon(icon), name, QVariant(data))
        else:
            combo.addItem(name, QVariant(data))

    def addComboSeparator(self, combo):
        combo.insertSeparator(combo.count())
    
    #
    # View manipulation
    #
    
    def updateView(self):
        for mapping in self.mappings:
            mapping.updateView(self.model)
    
    #
    # Mapping helpers
    #
    
    def registerRadioMapping(self, *args):
        self.mappings.append(RadioMapping(*args))
    
    def registerCheckMapping(self, *args):
        self.mappings.append(CheckMapping(*args))
    
    def registerComboMapping(self, *args):
        self.mappings.append(ComboMapping(*args))
    
    def registerTextMapping(self, *args):
        self.mappings.append(TextMapping(*args))
    
    def registerColorChooserMapping(self, *args):
        self.mappings.append(ColorChooserMapping(*args))

class Mapping(object):
    def __init__(self, key):
        self.key = key

    def updateView(self, config):
        self.updateViewValue(getattr(config, self.key))

class RadioMapping(Mapping):
    def __init__(self, key, radiobuttonswithvalues):
        Mapping.__init__(self, key)
        self.radiobuttonswithvalues = radiobuttonswithvalues

    def updateViewValue(self, value):
        for radiobutton, correspondingvalue in self.radiobuttonswithvalues.items():
            radiobutton.setChecked(value == correspondingvalue)

class CheckMapping(Mapping):
    def __init__(self, key, checkbox):
        Mapping.__init__(self, key)
        self.checkbox = checkbox
    
    def updateViewValue(self, value):
        self.checkbox.setChecked(value)
        
class ComboMapping(Mapping):
    def __init__(self, key, combobox):
        Mapping.__init__(self, key)
        self.combobox = combobox
    
    def updateViewValue(self, value):
        for n in range(0, self.combobox.count()):
            if self.combobox.itemData(n).toPyObject() == value:
                self.combobox.setCurrentIndex(n)
                return
        
        raise AssertionError("The value %s was not in the list of options" % value)
        
class TextMapping(Mapping):
    def __init__(self, key, lineedit):
        Mapping.__init__(self, key)
        self.lineedit = lineedit
    
    def updateViewValue(self, value):
        self.lineedit.setText(value)
        
class ColorChooserMapping(Mapping):
    def __init__(self, key, button):
        Mapping.__init__(self, key)
        self.button = button
    
    def updateViewValue(self, value):
        r, g, b = pinyin.utils.parseHtmlColor(value)
        
        p = self.button.palette()
        p.setColor(QPalette.ButtonText, QColor(r, g, b))