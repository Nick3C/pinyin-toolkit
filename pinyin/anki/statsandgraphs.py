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

from ankiqt.ui.graphs import AdjustableFigure, GraphWindow
import anki.utils

import hooks

from pinyin.logger import log
import pinyin.statistics


class HanziGraphHook(hooks.Hook):
    # Color Gradient for HSK score: http://gotomy.com/color.html to find a smooth gradient
    gradeColorsShortNames = {
        u'HSK Basic'        : (u'#FF0033', "Basic"),
        u'HSK Elementary'   : (u'#CC0066', "Element."),
        u'HSK Intermediate' : (u'#990099', "Intermed."),
        u'HSK Advanced'     : ('#6600CC', "Advanced"),
        u'Non-HSK'          : (u'#3300FF', "Non-HSK")
      }
    
    # Returns the Hanzi Figure object for the plot
    def calculateHanziData(self, graphwindow, hanzidata, days):
        log.info("Calculating %d days worth of Hanzi graph data", days)
        
        # NB: must lazy-load matplotlib to give Anki a chance to set up the paths
        # to the data files, or we get an error like "Could not find the matplotlib
        # data files" as documented at <http://www.py2exe.org/index.cgi/MatPlotLib>
        try:
            from matplotlib.figure import Figure
        except UnicodeEncodeError:
            # Haven't tracked down the cause of this yet, but reloading fixes it
            log.warn("UnicodeEncodeError loading matplotlib - trying again")
            from matplotlib.figure import Figure
        
        # Use the statistics engine to generate the data for graphing.
        # NB: should add one to the number of days because we want to
        # return e.g. 8 days of data for a 7 day plot (the extra day is "today").
        xs, _totaly, gradeys = pinyin.statistics.hanziDailyStats(hanzidata, days + 1)
        
        # Set up the figure into which we will add all our graphs
        figure = Figure(figsize=(graphwindow.dg.width, graphwindow.dg.height), dpi=graphwindow.dg.dpi)
        self.addLegend(figure)
        self.addGraph(figure, graphwindow, days, xs, gradeys)
        
        return figure

    def addLegend(self, figure):
        # Create the legend graph
        cheat = figure.add_subplot(111)
        bars, labels = [], []
        for n, grade in enumerate(pinyin.statistics.hanziGrades):
            gradeColor, gradeShortName = self.gradeColorsShortNames[grade]
            bars.append(cheat.bar(-3 - n, 0, color = gradeColor))
            labels.append(gradeShortName)
        
        # Add legend to the plot window
        cheat.legend(bars, labels, loc='upper left')
    
    def addGraph(self, figure, graphwindow, days, xs, gradeys):
        # Create the graph we will fill with the cumulative total information
        graph = figure.add_subplot(111)
        
        # Build all the x-y pairs that we are going to display: we want to show
        # a stacked area graph of the number of characters from each grade learnt over time
        colors, xys = [], []
        cumulative = [0 for _ in xs]
        for grade in pinyin.statistics.hanziGrades:
            # Increase the cumulative amount
            cumulative = [sofar + now for sofar, now in zip(cumulative, gradeys[grade])]
            colors.append(self.gradeColorsShortNames[grade][0])
            xys.append((xs, cumulative))

        # Add the final cumulative graph to the window.
        # NB: *reverse* lists to be displayed to get z-ordering correct
        flatxys = sum([[xs, ys] for xs, ys in xys[::-1]], [])
        graphwindow.dg.filledGraph(graph, days, colors[::-1], *flatxys)
        
        # NB: limits must be set AFTER we do filledGraph, or they aren't picked up.
        
        # Set the x values limits so we don't see the future or the far past
        graph.set_xlim(xmin=-days, xmax=0)

        # Set the minimum y value to be the smallest number of characters
        # in the range. Otherwise, if the number of hanzi you know didn't go
        # up too much in the given range, you'll get pretty much a rectangle
        # of a graph, which is not very useful
        if len(xs) > 0:
            firstcount = max([ys[0] for xs, ys in xys])
            lastcount = max([ys[len(ys) - 1] for xs, ys in xys])
            
            # NB: add 10 to the padding or the graph stuff may throw a wobbly
            # because the ymin and ymax are too close together (if there hasn't been
            # anything learned recently).
            padding = 10 + ((lastcount - firstcount) / 10)
            graph.set_ylim(ymin=max(0, firstcount - padding), ymax=lastcount + padding)

    def prepareHanziData(self):
        log.info("Retrieving Hanzi graph data")
        
        # Find models in this deck with the correct tag. NB: must do a 'like' because we want
        # to match tags like "Vocab Mandarin" as well as plain "Mandarin"
        mids = self.mw.deck.s.column0('select id from models where tags like "%%%s%%"' % self.config.modelTag)
        if len(mids) == 0:
            return None
        
        # Retrieve information about the card contents that were first answered on each day
        #
        # NB: the KanjiGraph uses information from ANY field (i.e. does not look at the fieldModels.name
        # value at all). However, Nick was confused by this behaviour because he had some radicals in his
        # deck, so his graph looked like he had `learnt' thousands of characters based on the listing of
        # every character in the `examples' fields of his radical facts.
        #
        # NB: the first answered time can be 0 but repeats > 1 due to a bug in an Anki feature which will
        # have screwed up the data in old decks. Exclude such data: <http://github.com/batterseapower/pinyin-toolkit/issues/closed/#issue/48>
        return self.mw.deck.s.all("""
        select value, firstAnswered from cards, fields, fieldModels, facts
        where
        cards.reps > 0 and
        cards.firstAnswered != 0 and
        cards.factId = fields.factId
        and cards.factId = facts.id
        and facts.modelId in %s
        and fields.fieldModelId = fieldModels.id
        and fieldModels.name in %s
        order by firstAnswered
        """ % (anki.utils.ids2str(mids), self.toSqlLiteral(self.config.candidateFieldNamesByKey['expression'])))

    def toSqlLiteral(self, thing):
        if isinstance(thing, list):
            return "(" + ",".join([self.toSqlLiteral(item) for item in thing]) + ")"
        elif isinstance(thing, basestring):
            # TODO: SQL escape??
            return u'"%s"' % thing
        elif isinstance(thing, int) or isinstance(thing, long):
            return unicode(thing)
        else:
            raise ValueError("Unsupported thing %s in SQL call", thing)

    def setupHanziGraph(self, graphwindow):
        log.info("Beginning setup of Hanzi graph on the graph window")
        
        # Preload data
        hanzidata = self.prepareHanziData()
        if hanzidata is None:
            # Don't add a graph if the deck doesn't have a Mandarin tag
            return
        
        # Append our own graph at the end
        extragraph = AdjustableFigure(graphwindow.parent, 'hanzi', lambda days: self.calculateHanziData(graphwindow, hanzidata, days), graphwindow.range)
        extragraph.addWidget(QtGui.QLabel("<h1>Unique Hanzi (Cumulative, By HSK Level)</h1>"))
        graphwindow.vbox.addWidget(extragraph)
        graphwindow.widgets.append(extragraph)
    
    def install(self):
        from anki.hooks import wrap
        
        log.info("Installing Hanzi graph hook")
        GraphWindow.setupGraphs = wrap(GraphWindow.setupGraphs, self.setupHanziGraph, "after")
