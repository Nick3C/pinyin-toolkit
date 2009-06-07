#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Notifier that actually displays the messages on screen.
"""
class AnkiNotifier(object):
    def __init__(self):
        # A list of those things we have already shown, if we're suppressing duplicate messages
        self.alreadyshown = []
    
    def info(self, what):
        import ankiqt.ui.utils
        ankiqt.ui.utils.showInfo(what)
    
    def infoOnce(self, what):
        if not(what in self.alreadyshown):
            self.info(what)
            self.alreadyshown.append(what)
    
    def exception(self, text, exception):
        import ankiqt.ui.utils
        ankiqt.ui.utils.showWarning(text + u"\r\nThe exception was:\r\n" + unicode(exception))
