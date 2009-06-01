def chooseField(candidateFieldNames, fact):
    # Find the first field that is present in the fact
    for candidateField in candidateFieldNames:
        if candidateField in fact.keys():
            return candidateField
    
    # No suitable field found!
    return None

def needmeanings(config):
    return config.meaninggeneration or config.detectmeasurewords