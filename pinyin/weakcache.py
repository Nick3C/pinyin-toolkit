import weakref

class WeakCache(object):
    def __init__(self, factory):
        self.__factory = factory
        self.__cache = {}
        self.__lastaccessed = None
    
    def __getitem__(self, key):
        # Obtain the saved weak reference, if any
        valueref = self.__cache.get(key)
        if valueref is not None:
            # Dereference the weak reference
            value = valueref()
            if value is not None:
                return value
        
        # Fall back on manufacturing the item again
        value = self.__factory(key)
        
        # Save that value into the cache weakly and ALSO save a strong
        # reference to it on the class.  This ensures that the last thing
        # we have touched will never be discarded - essential!
        self.__cache[key] = weakref.ref(value)
        self.__lastaccessed = value
        return value

if __name__ == "__main__":
    import unittest
    
    class Singleton(object):
        def __init__(self, value):
            self.value = value
    
    class WeakCacheTest(unittest.TestCase):
        def testGet(self):
            cache = WeakCache(lambda key: Singleton(key))
            
            one = cache["Hello!"]
            self.assertEquals(one.value, "Hello!")
            self.assertEquals(cache["Hello!"], one)
        
    unittest.main()
        