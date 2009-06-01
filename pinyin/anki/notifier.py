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

"""
A notifier used in tests.
"""
class MockNotifier(object):
    def __init__(self):
        self.infos = []
    
    def info(self, what):
        self.infos.append(what)
    
    def infoOnce(self, what):
        # Don't distinguish between once and many for now
        self.infos.append(what)