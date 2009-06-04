#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pinyin.config
from pinyin.languages import languages

class PreferencesController(object):
    def __init__(self, view, initialconfig):
        # Clone the configuration so we can change it at will
        self.model = pinyin.config.Config(initialconfig.settings)
    
        # Save the view (typically a Preferences instance) for later reference
        self.view = view
        
        self.setUpText()
    
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
                    self.view.addComboSeparator(self.view.controls.languageCombo)
                lastsupportlevel = supportlevel
            
                # Decide on the icon to use, if any
                if countrycode:
                    icon = ":/flags/%s.png" % countrycode
                else:
                    icon = None
            
                # Set the langcode as the user data for the combo item - this
                # will be picked up by the ComboMapping stuff
                self.view.addComboItem(self.view.controls.languageCombo, icon, name, langcode)
            
            self.registerCheckMapping("detectmeasurewords", self.view.controls.seperateMeasureWordCheck)
            
            self.registerComboMapping("dictlanguage", self.view.controls.languageCombo)
            
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
    
    def registerRadioMapping(self, key, radiobuttonswithvalues):
        pass
    
    def registerCheckMapping(self, key, checkbox):
        pass
    
    def registerComboMapping(self, key, combobox):
        pass
    
    def registerTextMapping(self, key, lineedit):
        pass
    
    def registerColorChooserMapping(self, key, button):
        pass