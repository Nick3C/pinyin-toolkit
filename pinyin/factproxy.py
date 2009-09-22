# -*- coding: utf-8 -*-

from pinyin.logger import log

"""
The fact proxy is responsible for making an Anki fact look like a dictionary with known keys.
It is responsible for choosing which of the available fields on a fact we map to each purpose.
"""
class FactProxy(object):
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
        for factfieldname in [factfieldname for factfieldname in fact.keys() if factfieldname.lower() == candidateField.lower()]:
            log.info("Choose %s as a field name from the fact for %s", factfieldname, candidateField)
            return factfieldname
    
    # No suitable field found!
    log.warn("No field matching %s in the fact", candidateFieldNames)
    return None
