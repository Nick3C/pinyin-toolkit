#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from pinyin.logger import log
import pinyin.forms.generated.builddb


# Based on AddCards dialog from Anki.  AddCards was:
#   Copyright: Damien Elmes <anki@ichi2.net>
#   License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
class BuildDB(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent, Qt.Window)
        self.parent = parent
        self.fieldWidgets = {}
        
        self.controls = pinyin.forms.generated.builddb.Ui_BuildDB()
        self.controls.setupUi(self)

if __name__ == "__main__":
    import sys
    import time
    import pinyin.forms.builddbcontroller
    import pinyin.mocks
    
    class MockDBBuilder(object):
        def build(self):
            print "Building!"
            time.sleep(5)
            print "Building done"
    
    app = QApplication(sys.argv)

    parent = QWidget()
    parent.resize(250, 150)
    parent.setWindowTitle('simple')
    
    builddb = BuildDB(parent)
    _controller = pinyin.forms.builddbcontroller.BuildDBController(builddb, pinyin.mocks.NullNotifier(), MockDBBuilder(), True)
    
    builddb.show()
    
    sys.exit(app.exec_())