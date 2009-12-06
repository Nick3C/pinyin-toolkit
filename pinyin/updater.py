# -*- coding: utf-8 -*-

import os

import config
from db import database
import dictionary
import dictionaryonline
import factproxy
import media
import meanings
import numbers
import model
import transformations
import updatergraph
import utils
import random
import re

from logger import log


# TODO:
#  * Only update fields that could have been changed by the update (quite important for audio!)
#  * (Perhaps) record hash in generated tag, so we can avoid recomputing more generally
#  * Make updating itself faster: e.g. prefer audio that already exists in the Anki deck

class FieldUpdater(object):
    def __init__(self, field, *args):
        self.field = field
        self.graphbasedupdater = updatergraph.GraphBasedUpdater(*args)
        self.reformatter = updatergraph.Reformatter(*args)

    def updatefact(self, fact, value, alwaysreformat=False):
        assert self.field in fact
        
        # HACK ALERT: can't think of a nicer way to do mwfieldinfact
        # NB: this is not quite right. The user might have changed whether there is a mw field independently of whether the
        # contents of the field we are considering has changed. However, this bug should be very hard to hit (TODO: fix it).
        delta = value is not None and { self.field : value, "mwfieldinfact" : "mw" in fact } or {}
        graph = self.graphbasedupdater.filledgraph(fact, delta)

        # For the same reason that fields may be missing from the graph but present in the fact,
        # even the field we are updating can be missing. For example, this happens when tabbing
        # away from a generated field.
        if self.field in graph:
            # EAGERLY reformat to produce the new value, which we plop back into the graph again so
            # other computations can see it. Note that this is potentially unsafe because we might now actually
            # need to recompute other thunks in the graph that depended on this one. Thankfully, right now
            # we only have updaters that guarantee not to change the value of an expression which will change
            # the value of anything *they* force to FIND that new value, so it works out.
            fact[self.field] = self.reformatter.reformatfield(self.field, graph, alwaysreformat=alwaysreformat)
            graph[self.field] = (False, utils.Thunk(lambda: fact[self.field]))

        log.info("Keys in the graph after update: %r", graph.keys())
        
        for field in fact:
            # Fields can be missing from the graph if they are generated fields in the input fact that
            # the graph failed to find a way to update. This really does happen!
            if shouldupdatefield(self.graphbasedupdater.config)(field) and field in graph:
                fact[field] = (graph[field][0] and factproxy.markgeneratedfield or (lambda x: x))(graph[field][1]())

class FieldUpdaterFromExpression(FieldUpdater):
    def __init__(self, *args):
        FieldUpdater.__init__(self, "expression", *args)
    
    def updatefact(self, fact, expression, **kwargs):
        # AutoBlanking Feature - If there is no expression, zeros relevant fields
        if expression != None and expression.strip() == u"":
            for field in self.graphbasedupdater.updateablefields:
                if field in fact and factproxy.isgeneratedfield(field, fact[field]):
                    fact[field] = u""
            
            # TODO: Nick added this to give up after auto-blanking. He claims it removes a minor
            # delay, but I'm not sure where the delay originates from, which worries me:
            return
        
        FieldUpdater.updatefact(self, fact, expression, **kwargs)

def shouldupdatefield(theconfig):
    return lambda field: config.updatecontrolflags[field] is None or theconfig.settings[config.updatecontrolflags[field]]
