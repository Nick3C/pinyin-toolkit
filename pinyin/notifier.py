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