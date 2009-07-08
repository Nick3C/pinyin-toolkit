#!/usr/bin/env python
# -*- coding: utf-8 -*-

import anki.utils

from pinyin.logger import log

"""
The fact proxy is responsible for making an Anki fact look like a dictionary with known keys.
It is responsible for choosing which of the available fields on a fact we map to each purpose.
"""
class AnkiFactProxy(object):
    def __init__(self, candidateFieldNamesByKey, fact):
        self.fact = fact
        
        # NB: the fieldnames dictionary IS part of the interface of this class
        self.fieldnames = {}
        for key, candidateFieldNames in candidateFieldNamesByKey.items():
            # Don't add a key into the dictionary if we can't find a field, or we end
            # up reporting that we the contain the field but die during access
            fieldname = chooseField(candidateFieldNames, fact)
            if fieldname is not None:
                self.fieldnames[key] = fieldname

    def __contains__(self, key):
        return key in self.fieldnames

    def __getitem__(self, key):
        return self.fact[self.fieldnames[key]]
    
    def __setitem__(self, key, value):
        self.fact[self.fieldnames[key]] = value

def chooseField(candidateFieldNames, fact):
    # Find the first field that is present in the fact
    for candidateField in candidateFieldNames:
        if candidateField in fact.keys():
            log.info("Choose %s as a field name from the fact", candidateField)
            return candidateField
    
    # No suitable field found!
    log.warn("No field matching %s in the fact", candidateFieldNames)
    return None

def persistconfig(mw, config):
    # NB: MUST store a dict into settings, not a Config object. The
    # reason is that the pickler needs to see the class definition
    # before it can unpickle, and Anki does the unpickling before
    # plugins get a chance to run :-(
    #
    # However, because we can't pickle the Config directly we need to make sure the Anki
    # configuration is updated with the new value whenever we modify the config.
    mw.config["pinyintoolkit"] = config.settings

def suitableFacts(modelTag, deck):
    for model in deck.models:
        if anki.utils.findTag(modelTag, model.tags):
            for fact in deck.s.query(anki.facts.Fact).filter('modelId = %s' % model.id):
                yield fact

if __name__ == "__main__":
    import unittest
    
    class AnkiFactProxyTest(unittest.TestCase):
        def testDontContainMissingFields(self):
            self.assertFalse("key" in AnkiFactProxy({"key" : ["Foo", "Bar"]}, { "Baz" : "Hi" }))
        
        def testContainsPresentFields(self):
            self.assertFalse("key" in AnkiFactProxy({"key" : ["Foo", "Bar"]}, { "Bar" : "Hi" }))
        
        def testSet(self):
            fact = { "Baz" : "Hi" }
            AnkiFactProxy({"key" : ["Foo", "Bar"]}, fact)["key"] = "Bye"
            self.assertEquals(fact["Baz"], "Bye")
        
        def testGet(self):
            fact = { "Baz" : "Hi" }
            self.assertEquals(AnkiFactProxy({"key" : ["Foo", "Bar"]}, fact)["key"], "Hi")
        
        def testPriority(self):
            fact = { "Baz" : "Hi", "Foo" : "Meh" }
            AnkiFactProxy({"key" : ["Foo", "Bar"]}, fact)["key"] = "Bye"
            self.assertEquals(fact["Foo"], "Bye")
            self.assertEquals(fact["Bar"], "Hi")
    
    unittest.main()