"""
A notifier used in tests.
"""
class MockNotifier(object):
    def __init__(self):
        self.infos = []
        self.exceptions = []
    
    def info(self, what):
        self.infos.append(what)
    
    def infoOnce(self, what):
        # Don't distinguish between once and many for now
        self.infos.append(what)
    
    def exception(self, text, exception_info=None):
        self.exceptions.append((text, exception_info))

"""
A notifier used in the live previewer.
"""
class NullNotifier(object):
    def info(self, *args):
        pass
    
    def infoOnce(self, *args):
        pass
    
    def exception(self, *args):
        pass

"""
A media manager used in tests and the live preview functionality.
"""
class MockMediaManager(object):
    def __init__(self, mediapacks, mediadir="dummy_dir", alreadyimported=[]):
        self._mediadir = mediadir
        self._mediapacks = mediapacks
        self._alreadyimported = alreadyimported
    
    def mediadir(self):
        return self._mediadir
    
    def discovermediapacks(self):
        return self._mediapacks
    
    def importtocurrentdeck(self, filename):
        return filename
    
    def alreadyimported(self, path):
        return path in self._alreadyimported