#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pinyin.logger import log

"""
The fact proxy is responsible for making an Anki fact look like a dictionary with known keys.
It is responsible for choosing which of the available fields on a fact we map to each purpose.
"""
class AnkiFactProxy(object):
    def __init__(self, candidateFieldNamesByKey, fact):
        self.fact = fact
        # NB: the fieldnames dictionary IS part of the interface of this class
        self.fieldnames = dict([(key, chooseField(candidateFieldNames, fact)) for key, candidateFieldNames in candidateFieldNamesByKey.items()])

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