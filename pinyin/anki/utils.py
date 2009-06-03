#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pinyin.logger import log

def chooseField(candidateFieldNames, fact):
    # Find the first field that is present in the fact
    for candidateField in candidateFieldNames:
        if candidateField in fact.keys():
            log.info("Choose %s as a field name from the fact", candidateField)
            return candidateField
    
    # No suitable field found!
    log.warn("No field matching %s in the fact", candidateFieldNames)
    return None
