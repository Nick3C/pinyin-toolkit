from logger import log

"""
Pinyin Toolkit configuration object: this will be pickled
up and stored into Anki's configuration database.  To allow
extension of this class in the future, I only pickle up the
key/value pairs stored in the user data field.
"""
class Config(object):
    def __init__(self, settings):
        # This constructor is a temporary crutch while I convert to using Anki's settings store:
        # in general, this object should be created using unpickling
        log.info("Initialized configuration with settings %s", settings)
        self.__dict__["settings"] = settings # Bypass __setattr__
    
    #
    # The pickle protocol (http://docs.python.org/library/pickle.html#pickle.Pickler)
    #
    
    def __getstate__(self):
        return self.settings
    
    def __setstate__(self, settings):
        self.__dict__["settings"] = settings
    
    #
    # Derived settings
    #
    
    needmeanings = property(lambda self: self.meaninggeneration or self.detectmeasurewords)
    
    #
    # Attribute protocol
    #
    
    def __getattr__(self, name):
        #print name
        #print self.settings
        try:
            return self.__dict__["settings"][name]
        except KeyError:
            raise AttributeError()

    def __setattr__(self, what, value):
        self.__dict__["settings"][what] = value

if __name__=='__main__':
    import unittest
    
    class ConfigTest(unittest.TestCase):
        def testPickle(self):
            import pickle
            config = Config({ "setting" : "value", "cheese" : "mice" })
            self.assertEquals(pickle.loads(pickle.dumps(config)).settings, config.settings)
    
        def testAttribute(self):
            self.assertEquals(Config({ "key" : "value" }).key, "value")
        
        def testIndexedAttribute(self):
            self.assertEquals(Config({ "key" : ["value"] }).key[0], "value")
    
        def testMissingAttribute(self):
            self.assertRaises(AttributeError, lambda: Config({ "key" : ["value"] }).kay)
    
    unittest.main()