#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtCore import QVariant, SIGNAL
from PyQt4.QtGui import QButtonGroup, QColor, QIcon, QPalette

import pinyin.config
from pinyin.languages import languages
import pinyin.media
import pinyin.mocks
import pinyin.updater
import pinyin.utils

import utils


previewexpression = u"书"
# Could also use:
#previewexpression = u"住宅樓"

# TODO: set media pack up up according to user extensions
previewmedia = [pinyin.media.MediaPack("Example", {"shu1.mp3" : "shu1.mp3"})]

class PreferencesController(object):
    def __init__(self, view, notifier, mediamanager, initialconfig):
        # Clone the configuration so we can change it at will
        self.model = pinyin.config.Config(initialconfig.settings)
    
        # Save the view (typically a Preferences instance) for later reference, along with other data
        self.view = view
        self.notifier = notifier
        self.mediamanager = mediamanager
        
        # Set up an updater we will use to deal with the live preview, based off the current model
        # NB: use NullNotifier instead of the one we are passed because we don't want e.g. popups about
        # installing sound packs if we are just doing the live preview!
        self.updater = pinyin.updater.FieldUpdater(pinyin.mocks.NullNotifier(), pinyin.mocks.MockMediaManager(previewmedia), self.model)
        
        # Set up the controls - one time only
        self.mappings = []
        self.setUpText()
        self.setUpColors()
        self.setUpAudio()

        # Use the mappings to reflect the initial setting values into the controls and preview pane
        self.updateView()
        self.updateViewPreview()
    
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
            
            self.registerCheckMapping("hanzimasking", self.view.controls.hanziMaskingCheck)
            
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
        
        setUpHanziPinyin()
        setUpMeanings()
    
    def setUpColors(self):
        # The Tone Colors panel
        def setUpToneColors():
            self.registerCheckMapping("colorizedpinyingeneration", self.view.controls.colorizePinyinCheck)
            
            for tone in range(1, 6):
                self.registerColorChooserMapping("tonecolors[%d]" % (tone - 1), getattr(self.view.controls, "tone%dButton" % tone))
        
        # The Quick Access Colors panel
        def setUpQuickAccessColors():
            helptext = "These colors, along with the tone colors, are available in the fact editor by pressing "\
                       "Ctrl+F1 to Ctrl+F8 while some text is selected - press Shift to get the sandhi variant:"
            if pinyin.utils.isosx():
                self.view.controls.quickAccessLabel.setText(helptext.replace("Ctrl", "Option"))
            else:
                self.view.controls.quickAccessLabel.setText(helptext)
        
            for shortcut in range(1, 4):
                self.registerColorChooserMapping("extraquickaccesscolors[%d]" % (shortcut - 1), getattr(self.view.controls, "quickAccess%dButton" % shortcut))
        
        # The Meaning Numbering Color panel
        def setUpMeaningNumberingColor():
            self.registerCheckMapping("colormeaningnumbers", self.view.controls.colorizeMeaningNumberingCheck)
            self.registerColorChooserMapping("meaningnumberingcolor", self.view.controls.meaningNumberingColorButton)
        
        setUpToneColors()
        setUpQuickAccessColors()
        setUpMeaningNumberingColor()
    
    def setUpAudio(self):
        self.registerCheckMapping("audiogeneration", self.view.controls.enableAudioCheck)
        
        self.updateAudioPacksList()
        
        # Connect up the two buttons to the event handlers
        self.view.connect(self.view.controls.installMandarinSoundsButton, SIGNAL("clicked()"), lambda: self.installMandarinSounds())
        self.view.connect(self.view.controls.openAudioPackDirectoryButton, SIGNAL("clicked()"), lambda: self.openAudioPackDirectory())
    
    def addComboItem(self, combo, icon, name, data):
        if icon:
            combo.addItem(QIcon(icon), name, QVariant(data))
        else:
            combo.addItem(name, QVariant(data))

    def addComboSeparator(self, combo):
        combo.insertSeparator(combo.count())
    
    #
    # Tear down
    #
    
    def __del__(self):
        self.unregisterMappings()
    
    #
    # Audio related functionality
    #
    
    def updateAudioPacksList(self):
        self.view.controls.audioPacksList.clear()
        for mediapack in self.mediamanager.discovermediapacks():
            self.view.controls.audioPacksList.addItem(mediapack.summarize(self.model.audioextensions))
    
    def installMandarinSounds(self):
        pinyin.media.downloadAndInstallMandarinSounds(self.notifier, self.mediamanager, self.model)
        self.updateAudioPacksList()
    
    def openAudioPackDirectory(self):
        utils.openFolder(self.mediamanager.mediadir())
    
    #
    # View manipulation
    #
    
    def updateView(self):
        for mapping in self.mappings:
            mapping.updateView()
    
    def updateViewPreview(self):
        # Create a model fact that we will fill with information, as well
        # as a list of fields to put that information into
        fact = {}
        fieldnamesbykey = {}
        for key, candidatefieldnames in self.model.candidateFieldNamesByKey.items():
            fact[key] = u""
            fieldnamesbykey[key] = pinyin.utils.heador(candidatefieldnames, key.capitalize())
        
        # Update the fact using the current model configuration
        self.updater.updatefact(fact, previewexpression)
        
        # Pull together the name of the field and the contents it should have
        namedvalues = []
        for key, value in fact.items():
            namedvalues.append((fieldnamesbykey[key], value))
        
        # Done: give the named values to the view, sorted by the field name
        self.view.updateFields(sorted(namedvalues, pinyin.utils.byFirst))

    #
    # Mapping helpers
    #
    
    def registerRadioMapping(self, *args):
        self.registerMapping(RadioMapping(self.model, *args))
    
    def registerCheckMapping(self, *args):
        self.registerMapping(CheckMapping(self.model, *args))
    
    def registerComboMapping(self, *args):
        self.registerMapping(ComboMapping(self.model, *args))
    
    def registerTextMapping(self, *args):
        self.registerMapping(TextMapping(self.model, *args))
    
    def registerColorChooserMapping(self, *args):
        self.registerMapping(ColorChooserMapping(self.model, lambda initcolor: self.view.pickColor(initcolor), *args))

    def registerMapping(self, mapping):
        # Ensure that we update the view whenever any of the mappings changes the model
        mapping.modelchanged.subscribe(self.updateViewPreview)
        
        self.mappings.append(mapping)

    def unregisterMappings(self):
        # Ensure that we remove the event handlers we install during registration,
        # to avoid memory leaks and other nasty stuff
        for mapping in self.mappings:
            mapping.modelchanged.unsubscribe(self.updateViewPreview)

class Event(object):
    def __init__(self):
        self.subscribers = []
    
    def subscribe(self, function):
        self.subscribers.append(function)
    
    def unsubscribe(self, function):
        self.subscribers.delete(function)
    
    def fire(self, *args, **kwargs):
        for subscriber in self.subscribers:
            subscriber(*args, **kwargs)

class Mapping(object):
    def __init__(self, model, key):
        self.model = model
        self.key = key
        
        self.modelchanged = Event()

    def updateView(self):
        self.updateViewValue(eval("model." + self.key, { "model" : self.model }))

    def updateModelValue(self, value):
        exec ("model." + self.key + " = value") in { "model" : self.model, "value" : value }
        self.modelchanged.fire()

class RadioMapping(Mapping):
    def __init__(self, model, key, radiobuttonswithvalues):
        Mapping.__init__(self, model, key)
        self.radiobuttonswithvalues = radiobuttonswithvalues
        
        buttongroup = None
        for radiobutton, correspondingvalue in self.radiobuttonswithvalues.items():
            # Tiresome extra setup to ensure that exactly one button is ever checked
            if buttongroup is None:
                buttongroup = QButtonGroup(radiobutton.parent())
            buttongroup.addButton(radiobutton)
            
            # NB: default-argument indirection below to solve closure capture issues
            radiobutton.connect(radiobutton, SIGNAL("clicked()"), lambda cv=correspondingvalue: self.updateModelValue(cv))

    def updateViewValue(self, value):
        for radiobutton, correspondingvalue in self.radiobuttonswithvalues.items():
            radiobutton.setChecked(value == correspondingvalue)

class CheckMapping(Mapping):
    def __init__(self, model, key, checkbox):
        Mapping.__init__(self, model, key)
        self.checkbox = checkbox
        
        self.checkbox.connect(self.checkbox, SIGNAL("clicked()"), lambda: self.updateModel())
    
    def updateModel(self):
        self.updateModelValue(self.checkbox.isChecked())
    
    def updateViewValue(self, value):
        self.checkbox.setChecked(value)
        
class ComboMapping(Mapping):
    def __init__(self, model, key, combobox):
        Mapping.__init__(self, model, key)
        self.combobox = combobox
        
        self.combobox.connect(self.combobox, SIGNAL("currentIndexChanged(int)"), lambda n: self.updateModel(n))
    
    def updateModel(self, n):
        self.updateModelValue(utils.fromQVariant(self.combobox.itemData(n)))
    
    def updateViewValue(self, value):
        for n in range(0, self.combobox.count()):
            if utils.fromQVariant(self.combobox.itemData(n)) == value:
                self.combobox.setCurrentIndex(n)
                return
        
        raise AssertionError("The value %s was not in the list of options" % value)
        
class TextMapping(Mapping):
    def __init__(self, model, key, lineedit):
        Mapping.__init__(self, model, key)
        self.lineedit = lineedit
        
        self.lineedit.connect(self.lineedit, SIGNAL('textEdited()'), lambda: self.updateModel())
    
    def updateModel(self):
        self.updateModelValue(self.lineedit.text())
    
    def updateViewValue(self, value):
        self.lineedit.setText(value)
        
class ColorChooserMapping(Mapping):
    def __init__(self, model, pickcolor, key, button):
        Mapping.__init__(self, model, key)
        self.button = button
        self.pickcolor = pickcolor
        
        self.button.connect(self.button, SIGNAL("clicked()"), lambda: self.updateModel())
    
    def palette(self):
        return self.button.palette()
    
    def setPalette(self, palette):
        self.button.setPalette(palette)
        
        # Modifying the palette seems to require an explicit repaint
        self.button.update()
    
    def updateModel(self):
        color = self.pickcolor(self.palette().color(QPalette.ButtonText))
        
        # The isValid flag is cleared if the user cancels the dialog
        if color != None and color.isValid():
            value = pinyin.utils.toHtmlColor(color.red(), color.green(), color.blue())
            self.updateModelValue(value)
            self.updateViewValue(value)
    
    def updateViewValue(self, value):
        r, g, b = pinyin.utils.parseHtmlColor(value)
        
        # NB: modifying the palette inplace works fine on windows, but fails miserably
        # on Windows. To be cross-platform, make sure we save the `modified' palette back.
        palette = self.palette()
        palette.setColor(QPalette.ButtonText, QColor(r, g, b))
        self.setPalette(palette)

