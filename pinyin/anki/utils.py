# -*- coding: utf-8 -*-

import anki.utils

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
