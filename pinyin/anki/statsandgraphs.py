#!/usr/bin/python
#-*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# This is a plugin for Anki: http://ichi2.net/anki/
# It is part of the Pinyin Toolkit plugin.
#
# This file is modifed from the version 1.0 of the:
# Kanji Graph Plugin by Anton Zolotkov <azolotkov@gmail.com>
# And has been hacked to work for Chinese
#
# License:     GNU GPL
# ---------------------------------------------------------------------------

from PyQt4 import QtGui

import time

try:
    from matplotlib.figure import Figure
except UnicodeEncodeError:
    # haven't tracked down the cause of this yet, but reloading fixes it
    from matplotlib.figure import Figure

from ankiqt.ui.graphs import AdjustableFigure, GraphWindow
import anki.utils

import hooks

from pinyin.logger import log
import pinyin.statistics


class HanziGraphHook(hooks.Hook):
    # Returns the Hanzi Figure object for the plot
    def calculateHanziData(self, graphwindow, hanzidata, days=30):
        log.info("Calculating %d days worth of Hanzi graph data", days)
        
        # Use the statistics engine to generate the data for graphing
        x, y, gradeys = pinyin.statistics.hanziDailyStats(hanzidata, days)
        # TODO: use gradeys
        
        # Setup the graph we will fill with the information
        figure = Figure(figsize=(graphwindow.dg.width, graphwindow.dg.height), dpi=graphwindow.dg.dpi)
        graph = figure.add_subplot(111)
        graph.set_xlim(xmin=-days, xmax=0)
        
        # Set the minimum y value to be the smallest number of characters
        # in the range. Otherwise, if the number of hanzi you know didn't go
        # up too much in the given range, you'll get pretty much a rectangle
        # of a graph, which is not very useful
        if len(y) > 1:
            lastcount = y[len(y) - 1]
            firstcount = y[0]
            
            # NB: add one to the ymax or else the graph stuff may throws a wobbly
            # because the ymin and ymax are too close together if there hasn't been
            # anything learned recently
            padding = (lastcount - firstcount) / 10
            graph.set_ylim(ymin=max(0, firstcount - padding), ymax=lastcount + padding + 1)

        # Add the final graph to the window
        graphwindow.dg.filledGraph(graph, days, "#fdce51", x, y)
        
        return figure

    def prepareHanziData(self):
        log.info("Retrieving Hanzi graph data")
        
        # Find models in this deck with the correct tag
        mids = self.mw.deck.s.column0('select id from models where tags like "%s"' % self.config.modelTag)
        if len(mids) == 0:
            return None
        
        # Retrieve information about the card contents that were first answered on each day
        return self.mw.deck.s.all("""
        select value, firstAnswered from cards, fields, facts
        where
        cards.reps > 0 and
        cards.factId = fields.factId
        and cards.factId = facts.id
        and facts.modelId in %s
        order by firstAnswered
        """ % anki.utils.ids2str(mids))

    def setupHanziGraph(self, graphwindow):
        log.info("Beginning setup of Hanzi graph on the graph window")
        
        # Preload data
        hanzidata = self.prepareHanziData()
        if hanzidata is None:
            # Don't add a graph if the deck doesn't have a Mandarin tag
            return
        
        # Append our own graph at the end
        extragraph = AdjustableFigure(graphwindow.parent, 'hanzi', lambda days: self.calculateHanziData(graphwindow, hanzidata, days), graphwindow.range)
        extragraph.addWidget(QtGui.QLabel("<h1>Cumulative Unique Hanzi Learned</h1>"))
        graphwindow.vbox.addWidget(extragraph)
        graphwindow.widgets.append(extragraph)
    
    def install(self):
        from anki.hooks import wrap
        
        log.info("Installing Hanzi graph hook")
        GraphWindow.setupGraphs = wrap(GraphWindow.setupGraphs, self.setupHanziGraph, "after")
