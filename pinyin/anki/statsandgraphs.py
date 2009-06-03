#!/usr/bin/python
#-*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# This is a plugin for Anki: http://ichi2.net/anki/
# 
# This file is modifed from the version 1.0 of the:
# Kanji Graph Plugin by Anton Zolotkov <azolotkov@gmail.com>
#
# It has been hacked to support Chinese instead of Japanese and merged into
# The Pinyin Toolkit
#
# License:     GNU GPL
# ---------------------------------------------------------------------------

from ankiqt import mw
from anki.stats import KanjiStats, isKanji

from PyQt4.QtGui import *
import time
from pinyin.logger import log

log.info("Hanzi graphs module loaded")

try:
    from matplotlib.figure import Figure
except UnicodeEncodeError:
    # haven't tracked down the cause of this yet, but reloading fixes it
    try:
        from matplotlib.figure import Figure
    except ImportError:
        pass
except ImportError:
    pass

from ankiqt.ui.graphs import GraphWindow
from ankiqt.ui.graphs import AdjustableFigure

from anki.graphs import DeckGraphs
from anki.utils import ids2str

class KanjiGraph(object):
  def __init__(self):

    # this function returns a tuple (days, kanjiCounts) where
    # days is a list of day indexes, negative, with 0 representing
    # today, and kanjiCounts is a list containing, for the corresponding
    # day, the number of kanji that the user has "learned" up until
    # the day, for some loose definition of "learn"
    def getKanjiDailyStats(self, daysInRange):
      self.genKanjiSets()

      mids = self.deck.s.column0("select id from fieldModels where name LIKE '%Mandarin%'")
      rows = self.deck.s.column0("""
select value, firstAnswered from cards, fields, facts
where
fieldModelID = :hid AND
cards.factId = fields.factId AND
cards.reps > 0 AND
hid=hanzi_id AND
cards.factId = fields.factId AND
facts.modelId in %s
order by firstAnswered
""" % ids2str(mids))

      # this dictionary holds, for each day, the string constructued
      # by appending values of all fields for the cards that were
      # first answered on the given day
      firstLearnedByDay = {}
      days = []
      endOfDay = time.time()
      for (value, firstAnswered) in rows:
        # FIXME: this doesn't account for midnightOffset
        day = int((firstAnswered - endOfDay) / 86400.0)
        if firstLearnedByDay.has_key(day):
          firstLearnedByDay[day] = firstLearnedByDay[day] + value
        else:
          days.append(day);
          firstLearnedByDay[day] = value

      totalKanjiCountsByDay = {}
      # a little slow and ugly, but at least I got away with only one SQL query
      for kanjiSet in self.kanjiSets:
        for kanji in kanjiSet:
          # IMPORTANT: we need to iterate over days in order from earliest to latest,
          # because we want to make sure that we only count the earliest time we
          # encountered a given kanji
          for day in days:
            if firstLearnedByDay[day].find(kanji) != -1:
                totalKanjiCountsByDay[day] = totalKanjiCountsByDay.get(day, 0) + 1
                break
            
            """
            if firstLearnedByDay[day].find(kanji) != -1:
              totalKanjiCountsByDay[day] = totalKanjiCountsByDay.get(day, 0) + 1
              grade = self.kanjiGrade(kanji)
              if grade != 0 and grade != 8:
                jouyouKanjiCountsByDay[day] = jouyouKanjiCountsByDay.get(day, 0) + 1
              
              # we have counted the kanji for the earliest day that it appeard in,
              # and now we move on to the next kanji (otherwise we might count it
              # again for another day that it shows up on, perhaps in a
              # different compound
              break
            """

      # convert the data into a format usable by the graphing platform
      x = []
      y = []
      totalKanjiCountSoFar = 0
      for day in days:
        totalKanjiCountSoFar += totalKanjiCountsByDay.get(day, 0)
        if day >= -daysInRange:
          x.append(day)
          y.append(totalKanjiCountSoFar)
                
      return (x, y)

    # add the function to the KanjiStats class
    KanjiStats.getKanjiDailyStats = getKanjiDailyStats

    # saving the original implementation
    GraphWindow.originalSetupGraphs = GraphWindow.setupGraphs

    def newSetupGraphs(self):
      # calling the original implementation
      GraphWindow.originalSetupGraphs(self)

      # and then appending our own graph at the end
      kanji = AdjustableFigure(self.parent, 'hanzi', self.dg.kanji, self.range)
      kanji.addWidget(QLabel(_("<h1>Hanzi</h1>")))
      self.vbox.addWidget(kanji)
      self.widgets.append(kanji)

    # overriding the original implementation with the new implementation
    GraphWindow.setupGraphs = newSetupGraphs

    # function that will return the kanji Figure object for the kanji plot
    def kanjiData(self, days=30):
      kanjiStats = KanjiStats(self.deck)
      (x, y) = kanjiStats.getKanjiDailyStats(days)
      fig = Figure(figsize=(self.width, self.height), dpi=self.dpi)
      graph = fig.add_subplot(111)
      self.filledGraph(graph, days, "#fdce51", x, y)
      graph.set_xlim(xmin=-days, xmax=0)
      # setting min y value to be the smallest number of kanji in the
      # range. Otherwise, if the number of kanji you know didn't go
      # up too much in the given range, you'll get pretty much a
      # rectangle of a graph, which is not very useful
      if len(y) > 1:
        padding = (y[len(y) - 1] - y[0]) / 10
        graph.set_ylim(ymin=max(0, y[0] - padding), ymax=y[len(y) - 1] + padding)

      return fig

    # dynamically appending the function to the class
    DeckGraphs.kanji = kanjiData


class KanjiGraphLauncher(object):
  def __init__(self, ankiMain):
    self.mw = ankiMain
    self.kanjiGraph = KanjiGraph()

  def pluginInit(self):
    return

def hookPluginInit():
  r.pluginInit()

if __name__ == "__main__":
  print "This is a plugin for Anki and cannot be run independently."
  print "Please download the latest version of Anki from http://ichi2.net/anki/"
  print "and copy this file into your ~/.anki/plugins directory."
else:
  r = KanjiGraphLauncher(mw)
  mw.addHook("init", hookPluginInit)

