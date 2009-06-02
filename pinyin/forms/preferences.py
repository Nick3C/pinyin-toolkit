# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import generated


class Preferences(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent, Qt.Window)
        self.parent = parent
        
        dialog = generated.preferences.Ui_Preferences()
        self.setupDialog(dialog)
        
        fieldsScroll = self.createFieldsScroll(dialog.fieldsArea)
        fieldsScroll.setWidget(self.createFieldsFrame(["Expression", "Reading", "Etc"]))
        
        self.show()
        
        # Necessary for Anki integration?
        # ui.dialogs.open("AddCards", self)
        
    def setupDialog(self, dialog):
        # Initialize
        dialog.setupUi(self)
        
        # Make the status background the same colour as the frame.
        palette = dialog.status.palette()
        c = unicode(palette.color(QPalette.Window).name())
        dialog.status.setStyleSheet("* { background: %s; color: #000000; }" % c)

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
        
        #self.parent.setUpdatesEnabled(True)
        return fieldsFrame

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    window = QWidget()
    window.resize(250, 150)
    window.setWindowTitle('simple')
    
    Preferences(window)
    #window.show()
    
    sys.exit(app.exec_())