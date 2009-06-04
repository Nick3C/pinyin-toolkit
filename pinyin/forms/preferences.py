#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from pinyin.logger import log
import pinyin.forms.generated.preferences


# Based on AddCards dialog from Anki.  AddCards was:
#   Copyright: Damien Elmes <anki@ichi2.net>
#   License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
class Preferences(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent, Qt.Window)
        self.parent = parent
        
        self.controls = pinyin.forms.generated.preferences.Ui_Preferences()
        self.controls.setupUi(self)
        
        fieldsScroll = self.createFieldsScroll(self.controls.fieldsFrame)
        fieldsScroll.setWidget(self.createFieldsFrame(["Expression", "Reading", "Etc"]))
        self.createButtonGroups()
        
        # Necessary for Anki integration?
        # ui.dialogs.open("AddCards", self)
    
    #
    # Setup
    #
    
    def createButtonGroups(self):
        # I've actually put these in the .ui file, but the pyuic4 thing can't import that data! Sigh...
        def makeButtonGroup(*buttons):
            group = QButtonGroup(self)
            for button in buttons:
                group.addButton(button)
        
        makeButtonGroup(self.controls.numericPinyinTonesRadio, self.controls.tonifiedPinyinTonesRadio)
        makeButtonGroup(self.controls.simplifiedHanziRadio, self.controls.traditionalHanziRadio)
        makeButtonGroup(self.controls.circledChineseNumberingRadio, self.controls.circledArabicNumberingRadio,
                        self.controls.plainNumberingRadio, self.controls.noNumberingRadio)
        makeButtonGroup(self.controls.linesSeperatorRadio, self.controls.commasSeperatorRadio, self.controls.customSeperatorRadio)
    
    def createFieldsScroll(self, widget):
        # scrollarea
        fieldsScroll = QScrollArea()
        fieldsScroll.setWidgetResizable(True)
        fieldsScroll.setLineWidth(0)
        fieldsScroll.setFrameStyle(0)
        fieldsScroll.setFocusPolicy(Qt.NoFocus)
        
        
        # top level vbox
        fieldsBox = QVBoxLayout(widget)
        fieldsBox.setMargin(0)
        fieldsBox.setSpacing(3)
        fieldsBox.addWidget(fieldsScroll)
        
        # button styles for mac
        widget.setStyle(QStyleFactory.create("plastique"))
        
        widget.setLayout(fieldsBox)
        
        return fieldsScroll

    def createFieldsFrame(self, fieldnames):
        #self.parent.setUpdatesEnabled(False)
        
        fieldsFrame = QWidget()
        fieldsGrid = QGridLayout(fieldsFrame)
        fieldsFrame.setLayout(fieldsGrid)
        fieldsGrid.setMargin(0)
        
        # add entries for each field
        for n, fieldname in enumerate(fieldnames):
            # label
            l = QLabel(fieldname)
            fieldsGrid.addWidget(l, n, 0)
            
            # edit widget
            w = QTextEdit(self)
            w.setTabChangesFocus(True)
            w.setAcceptRichText(True)
            w.setMinimumSize(20, 60)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            w.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            fieldsGrid.addWidget(w, n, 1)
        
        self.parent.setUpdatesEnabled(True)
        return fieldsFrame
    
    #
    # Interface with controller
    #
    
    def pickColor(self, initcolor):
        return QColorDialog.getColor(initcolor, self)

if __name__ == "__main__":
    import sys
    import pinyin.config
    import pinyin.forms.preferencescontroller
    
    app = QApplication(sys.argv)

    parent = QWidget()
    parent.resize(250, 150)
    parent.setWindowTitle('simple')
    
    preferences = Preferences(parent)
    pinyin.forms.preferencescontroller.PreferencesController(preferences, pinyin.config.Config({}))
    
    preferences.show()
    
    sys.exit(app.exec_())