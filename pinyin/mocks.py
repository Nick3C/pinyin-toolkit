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
    
    def exception(self, text, exception):
        self.exceptions.append((text, exception))

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
    def __init__(self, mediapacks, themediadir="dummy_dir"):
        self.themediadir = themediadir
        self.mediapacks = mediapacks
    
    def mediadir(self):
        return self.themediadir
    
    def discovermediapacks(self):
        return self.mediapacks
    
    def importtocurrentdeck(self, filename):
        return filename