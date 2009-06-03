# -*- coding: utf-8 -*-
# Shrunk version of color shortcut plugin merged with Pinyin Toolkit to give that functionality without the seperate download
# Original version by Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from anki.hooks import wrap, addHook
from ankiqt import mw
from ankiqt import ui
import ankiqt.ui.facteditor

from pinyin.logger import log
log.info("Shortcut keys module loaded")

"""
self.colorlist = self.config.colorlist


def setColor(widget, color):
    w = widget.focusedEdit()
    cursor = w.textCursor()
    new = QColor(color)
    w.setTextColor(new)
    cursor.clearSelection()
    w.setTextCursor(cursor)
    
def setallbuttons(buttonpush):
    # loop through the 12 F[x] keys, setting each one up with a shortcut
    i=1
    while i <= 12:
        seteachbutton(i,colorindex[i])
        i += 1
    
    
def seteachbutton(key, color):
    shortcut = "Ctrl+F" + key
    colbut[key] = QPushButton()
    colbut[key].connect(colbut[key], SIGNAL("clicked()"), lambda self=self: ShortColor[key](self,colorlist[key]))
    colbut[key].setText("1")
    colbut[key].setShortcut(shortcut)
    colbut[key].setFocusPolicy(Qt.NoFocus)
    colbut[key].setFixedSize(0,0)
    self.iconsBox.addWidget(colbut1)

"""