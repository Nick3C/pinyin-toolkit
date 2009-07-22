# -*- coding: utf-8 -*-

from PyQt4.QtCore import QThread, SIGNAL
from PyQt4.QtGui import QDialog

import cjklib
import sys

from pinyin.logger import log


def makerichtext(paragraphs):
    return """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
<head>
<meta name="qrichtext" content="1" />
<style type="text/css">
p, li { white-space: pre-wrap; }
</style>
</head>
<body style=" font-family:'Lucida Grande'; font-size:13pt; font-weight:400; font-style:normal;">
%s
</body>
</html>
""" % "<p></p>\n".join(['<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">' + paragraph + '</p>\n' for paragraph in paragraphs])

firstrunmessage = makerichtext([
    'Thanks for installing the Pinyin Toolkit!',
    '',
    'Because this is the first time you\'ve run Anki with the Toolkit installed, we need to create a database of Chinese readings and meanings. This will only happen once, and means that the toolkit will be blazing fast in day-to-day use.',
    '',
    'This might take a few minutes even on a modern PC - while you are waiting you might want to take a look at our <a href="http://batterseapower.github.com/pinyin-toolkit/getit.html"><span style=" text-decoration: underline; color:#0000ff;">setup guide</span></a>.',
    ''
  ])

updateddatabasemessage = makerichtext([
    'The Pinyin Toolkit is rebuilding its database of Chinese readings and meanings.',
    '',
    'This is happening because it looks like at least one of the source files for the database has been changed - perhaps you have just upgraded the toolkit?',
    ''
  ])

class BuildDBController(object):
    def __init__(self, view, notifier, dbbuilder, compulsory):
        # Reflect the initial setting values into the controls
        view.controls.explanationLabel.setText(compulsory and firstrunmessage or updateddatabasemessage)
        view.controls.cancelButtonBox.setEnabled(not(compulsory))
        
        # Create and run a thread that just constructs the database
        class Worker(QThread):
            def run(self):
                try:
                    dbbuilder.build()
                    self.emit(SIGNAL("buildsuccess()"))
                except Exception, e:
                    log.exception("Suppressed exception in database build process")
                    self.emit(SIGNAL("buildfailure(PyQt_PyObject)"), sys.exc_info())
        
        # NB: there is an EXTREMELY NASTY garbage collection bug lurking here. We need to
        # ensure that the QThread is not garbage collected or else we will get a segmentation
        # fault. This means that we must assign the thread as a member of self and make sure
        # that the BuildDBController is saved somewhere by >it's< user! Apparently this is
        # normal: <http://www.nabble.com/-python-Qt4-a-problem-of-QThread-td16993255.html>
        self.thread = Worker()
        
        def buildFailure(e):
            notifier.exception("There was an error while building the Pinyin Toolkit database!", e)
            view.done(QDialog.Rejected)
        
        view.connect(self.thread, SIGNAL("buildsuccess()"), lambda: view.done(QDialog.Accepted))
        view.connect(self.thread, SIGNAL("buildfailure(PyQt_PyObject)"), lambda e: buildFailure(e))
        
        # GO!
        self.thread.start()
