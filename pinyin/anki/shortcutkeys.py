# -*- coding: utf-8 -*-
# Shrunk version of color shortcut plugin merged with Pinyin Toolkit to give that functionality without the seperate download
# Original version by Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from anki.hooks import wrap,addHook
from ankiqt import mw
from ankiqt import ui
import ankiqt.ui.facteditor

def setColor(widget, color):
    w = widget.focusedEdit()
    cursor = w.textCursor()
    new = QColor(color)
    w.setTextColor(new)
    cursor.clearSelection()
    w.setTextCursor(cursor)

#define the colors you want to use here
def ShortColor1(self):
    setcolor(self, "#FF0000")
# default is #FF0000, red
def ShortColor2(self):
    setcolor(self, "#ffaa00")
# default is #ffaa00, orange
def ShortColor3(self):
    setcolor(self, "#00aa00")
# default is #00aa00, green
def ShortColor4(self):
    setcolor(self, "#0000FF")
# default is #0000FF, blue
def ShortColor5(self):
    setcolor(self, "##545454")
# default is #ffff00, grey
def ShortColor6(self):
    setcolor(self, "#00AAFF")
# default is #00AAFF, light blue
def ShortColor7(self):
    setcolor(self, "#000000")
# default is #000000, black [note this is not the same as no color]
def ShortColor8(self):
    setcolor(self, "#ffff00")
# default is #55007F, yellow
def ShortColor9(self):
    setcolor(self, "#FF00FF")
# default is #FF00FF, pink
def ShortColor0(self):
    setcolor(self, "#00AA7F")


def newFields(self):
    colbut1 = QPushButton()
    colbut1.connect(colbut1, SIGNAL("clicked()"), lambda self=self: ShortColor1(self))
    colbut1.setText("1")
    colbut1.setShortcut("Ctrl+F1")
    colbut1.setFocusPolicy(Qt.NoFocus)
    colbut1.setFixedSize(0,0)
    self.iconsBox.addWidget(colbut1)
    
    colbut2 = QPushButton()
    colbut2.connect(colbut2, SIGNAL("clicked()"), lambda self=self: ShortColor2(self))
    colbut2.setText("2")
    colbut2.setShortcut("Ctrl+F2")
    colbut2.setFocusPolicy(Qt.NoFocus)
    colbut2.setFixedSize(0,0)
    self.iconsBox.addWidget(colbut2)
    
    colbut3 = QPushButton()
    colbut3.connect(colbut3, SIGNAL("clicked()"), lambda self=self: ShortColor3(self))
    colbut3.setText("3")
    colbut3.setShortcut("Ctrl+F3")
    colbut3.setFocusPolicy(Qt.NoFocus)
    colbut3.setFixedSize(0,0)
    self.iconsBox.addWidget(colbut3)
    
    colbut4 = QPushButton()
    colbut4.connect(colbut4, SIGNAL("clicked()"), lambda self=self: ShortColor4(self))
    colbut4.setText("4")
    colbut4.setShortcut("Ctrl+F4")
    colbut4.setFocusPolicy(Qt.NoFocus)
    colbut4.setFixedSize(0,0)
    self.iconsBox.addWidget(colbut4)
    
    colbut5 = QPushButton()
    colbut5.connect(colbut5, SIGNAL("clicked()"), lambda self=self: ShortColor5(self))
    colbut5.setText("S")
    colbut5.setShortcut("Ctrl+F5")
    colbut5.setFocusPolicy(Qt.NoFocus)
    colbut5.setFixedSize(0,0)
    self.iconsBox.addWidget(colbut5)
    
    colbut6 = QPushButton()
    colbut6.connect(colbut6, SIGNAL("clicked()"), lambda self=self: ShortColor6(self))
    colbut6.setShortcut("Ctrl+F6")
    colbut6.setFocusPolicy(Qt.NoFocus)
    colbut6.setFixedSize(0,0)
    self.iconsBox.addWidget(colbut6)

    colbut7 = QPushButton()
    colbut7.connect(colbut7, SIGNAL("clicked()"), lambda self=self: ShortColor7(self))
    colbut7.setShortcut("Ctrl+F7")
    colbut7.setFocusPolicy(Qt.NoFocus)
    colbut7.setFixedSize(0,0)
    self.iconsBox.addWidget(colbut7)
    
    colbut8 = QPushButton()
    colbut8.connect(colbut8, SIGNAL("clicked()"), lambda self=self: ShortColor8(self))
    colbut8.setShortcut("Ctrl+F8")
    colbut8.setFocusPolicy(Qt.NoFocus)
    colbut8.setFixedSize(0,0)
    self.iconsBox.addWidget(colbut8)
    
#    colbut9 = QPushButton()
#    colbut9.connect(colbut9, SIGNAL("clicked()"), lambda self=self: ShortColor9(self))
#    colbut9.setShortcut("Ctrl+F9")
#    colbut9.setFocusPolicy(Qt.NoFocus)
#    colbut9.setFixedSize(0,0)
#    self.iconsBox.addWidget(colbut9)

#    colbut0 = QPushButton()
#    colbut0.connect(colbut0, SIGNAL("clicked()"), lambda self=self: ShortColor0(self))
#    colbut0.setShortcut("Ctrl+F10")
#    colbut0.setFocusPolicy(Qt.NoFocus)
#    colbut0.setFixedSize(0,0)
#    self.iconsBox.addWidget(colbut0)

ankiqt.ui.facteditor.FactEditor.setupFields = wrap(ankiqt.ui.facteditor.FactEditor.setupFields,newFields,"after")
newFields(mw.editor)
