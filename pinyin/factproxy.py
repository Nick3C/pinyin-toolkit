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
            fieldname = chooseField(candidateFieldNames, fact.keys())
            if fieldname is not None:
                self.fieldnames[key] = fieldname

    def __contains__(self, key):
        return key in self.fieldnames

    def __iter__(self):
        return self.fieldnames.keys().__iter__()

    def __getitem__(self, key):
        return self.fact[self.fieldnames[key]]
    
    def __setitem__(self, key, value):
        self.fact[self.fieldnames[key]] = value

def chooseField(candidateFieldNames, targetkeys):
    # Find the first field that is present in the fact
    for candidateField in candidateFieldNames:
        for factfieldname in [factfieldname for factfieldname in targetkeys if factfieldname.lower() == candidateField.lower()]:
            log.info("Choose %s as a field name from the fact for %s", factfieldname, candidateField)
            return factfieldname
    
    # No suitable field found!
    log.warn("No field matching %s in the fact", candidateFieldNames)
    return None


# Marker carefully chosen to be stable under munging by the Anki and QT HTML framework,
# as well as invisible to the user under ordinary conditions. Change this at your PERIL:
generatedmarker = '<a name="pinyin-toolkit"></a>'

def isblankfield(value):
    return len(value.strip()) == 0

def isgeneratedfield(key, value):
    return key == "weblinks" or value.startswith(generatedmarker)

def unmarkgeneratedfield(value):
    if value.startswith(generatedmarker):
        # NB: do NOT lstrip regardless of startswith, because lstrip even removes characters
        # if we have a partial match of the string - I had a bug where I was stripping leading
        # angle brackets out of fields containing HTML! Furthermore, lstrip attempts to strip
        # the string it is given SEVERAL times.
        return value[len(generatedmarker):]
    else:
        return value

def markgeneratedfield(value):
    return generatedmarker + value
