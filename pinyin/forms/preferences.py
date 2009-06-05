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
        
        self.fieldsScroll = self.createFieldsScroll(self.controls.fieldsFrame)
        
        # Necessary for Anki integration?
        # ui.dialogs.open("AddCards", self)
    
    #
    # Setup
    #
    
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

    #
    # Interface with controller
    #
    
    def pickColor(self, initcolor):
        return QColorDialog.getColor(initcolor, self)
    
    def updateFields(self, namedvalues):
        # Suspend repainting
        self.parent.setUpdatesEnabled(False)
        
        # Build font for fields
        font = QFont()
        font.setFamily("Arial")
        font.setPixelSize(20)
        
        # Construct a new frame to hold all the fields
        fieldsFrame = QWidget()
        fieldsGrid = QGridLayout(fieldsFrame)
        fieldsFrame.setLayout(fieldsGrid)
        fieldsGrid.setMargin(0)
        
        # Add entries for each field
        for n, (fieldname, fieldvalue) in enumerate(namedvalues):
            # Field label
            l = QLabel(fieldname)
            fieldsGrid.addWidget(l, n, 0)
            
            # Edit widget
            w = QTextEdit(self)
            w.setTabChangesFocus(True)
            w.setAcceptRichText(True)
            w.setMinimumSize(10, 0)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            w.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            w.setFont(font)
            w.setReadOnly(True)
            w.setText(fieldvalue)
            
            # Add the widget to the grid
            fieldsGrid.addWidget(w, n, 1)
        
        # Resume repainting
        self.parent.setUpdatesEnabled(True)
        
        # Display the fields on the actual form
        self.fieldsScroll.setWidget(fieldsFrame)
        fieldsFrame.show()
        self.fieldsScroll.show()

if __name__ == "__main__":
    import sys
    import pinyin.config
    import pinyin.dictionary
    import pinyin.forms.preferencescontroller
    import pinyin.mocks
    
    app = QApplication(sys.argv)

    parent = QWidget()
    parent.resize(250, 150)
    parent.setWindowTitle('simple')
    
    preferences = Preferences(parent)
    pinyin.forms.preferencescontroller.PreferencesController(preferences, pinyin.mocks.NullNotifier(), pinyin.mocks.MockMediaManager([]), pinyin.config.Config({}))
    
    preferences.show()
    
    sys.exit(app.exec_())