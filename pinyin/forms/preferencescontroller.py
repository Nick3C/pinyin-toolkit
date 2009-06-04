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
                self.view.numericPinyinTonesRadio : "numeric",
                self.view.tonifiedPinyinTonesRadio : "tonified"
              })
            
            self.registerRadioMapping("prefersimptrad", {
                self.view.simplifiedHanziRadio : "simp",
                self.view.traditionalHanziRadio : "trad"
              })
        
        # The Meanings panel
        def setUpMeanings():
            for support, langcode, countrycode, name in languages:
                if countrycode:
                    icon = QIcon(":/flags/%s.png" % countrycode)
                else:
                    icon = None
                
                # Set the langcode as the user data for the combo item - this
                # will be picked up by the ComboMapping stuff
                self.view.languageCombo.addItem(icon, name, langcode)
            
            self.registerCheckMapping("detectmeasurewords", self.view.seperateMeasureWordCheck)
            
            self.registerComboMapping("dictlanguage", self.view.languageCombo)
            
            self.registerRadioMapping("meaningnumbering", {
                self.view.circledChineseNumberingRadio : "circledChinese",
                self.view.circledArabicNumberingRadio : "circledArabic",
                self.view.plainNumberingRadio : "arabicParens",
                self.view.noNumberingRadio : "none",
              })
            
            self.registerRadioMapping("meaningseperator", {
                self.view.linesSeperatorRadio : "lines",
                self.view.commasSeperatorRadio : "commas",
                self.view.customSeperatorRadio : "custom"
              })
            
            self.registerTextMapping("custommeaningseperator", self.view.customSeperatorLineEdit)
        
        # The Tone Colors panel
        def testSetUpToneColors():
            self.registerCheckMapping("colorizedpinyingeneration", self.view.colorizeCheck)
            
            for tone in range(1, 6):
                self.registerColorChooserMapping("tone%dcolor" % tone, getattr(self.view, "tone%dButton" % tone))
        
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