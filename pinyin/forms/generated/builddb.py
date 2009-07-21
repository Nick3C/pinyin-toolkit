# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/builddb.ui'
#
# Created: Mon Jul 20 22:54:51 2009
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_BuildDB(object):
    def setupUi(self, BuildDB):
        BuildDB.setObjectName("BuildDB")
        BuildDB.resize(400, 260)
        self.verticalLayout_2 = QtGui.QVBoxLayout(BuildDB)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.explanationLabel = QtGui.QLabel(BuildDB)
        self.explanationLabel.setWordWrap(True)
        self.explanationLabel.setOpenExternalLinks(True)
        self.explanationLabel.setObjectName("explanationLabel")
        self.verticalLayout_2.addWidget(self.explanationLabel)
        self.progressBar = QtGui.QProgressBar(BuildDB)
        self.progressBar.setMaximum(0)
        self.progressBar.setProperty("value", QtCore.QVariant(-1))
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout_2.addWidget(self.progressBar)
        self.cancelButtonBox = QtGui.QDialogButtonBox(BuildDB)
        self.cancelButtonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel)
        self.cancelButtonBox.setObjectName("cancelButtonBox")
        self.verticalLayout_2.addWidget(self.cancelButtonBox)

        self.retranslateUi(BuildDB)
        QtCore.QMetaObject.connectSlotsByName(BuildDB)

    def retranslateUi(self, BuildDB):
        BuildDB.setWindowTitle(QtGui.QApplication.translate("BuildDB", "Build Pinyin Toolkit Database", None, QtGui.QApplication.UnicodeUTF8))

