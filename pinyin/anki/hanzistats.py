#!/usr/bin/python
#-*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# This is a plugin for Anki: http://ichi2.net/anki/
# It is part of the Pinyin Toolkit plugin.
#
# This file was modifed from the HanziStats plugin inofficial versions 0.08.1b and 0.08.2.
# The plugin is now maintained as part of Pinyin Toolkit by Nick Cook and Max Bolingbroke.
# Support requests should be sent to pinyintoolkit@gmail.com.
#
# The following people have worked on the code for Hanzi Stats prior to it merge with Pintin Toolkit. 
# Original Author:                    Hedge (c dot reksten dot monsen at gmail dot com)             
# Hack to Reference Text Files:       Junesun (yutian dot mei at gmail dot com)                       
# Innofficial 0.08.2 (Traditional):   JamesStrange at yahoo dot com
#
# License:     GNU GPL
# ---------------------------------------------------------------------------

import os
import codecs
import traceback
import sys

from PyQt4 import QtGui, QtCore
from ankiqt import mw

#  SETTINGS
#  Give file address if you want additional characters to be considered as learned
#  e. g. FILE = os.path.join(mw.config.configPath, "plugins", "known_hanzi.txt")
FILE = ""



def isKanji(unichar): 
    import unicodedata 
    try: 
        return unicodedata.name(unichar).find('CJK UNIFIED IDEOGRAPH') >= 0 

    except ValueError: 
        # A control character 
        return False 



####################################################################
#  Add Hanzi statisticts choice to the Tool menu.                  #
####################################################################
def init_hook():
  mw.mainWin.HanziStats = QtGui.QAction('Hanzi Statistics (PyTK)', mw)
  mw.mainWin.HanziStats.setStatusTip('Hanzi Statistics (PyTK)')
  mw.mainWin.HanziStats.setEnabled(True)
  mw.mainWin.HanziStats.setIcon(QtGui.QIcon("../icons/hanzi.png"))
  # the following line can be changed to customise your default view with the first zero after run representing simp/trad and the second seen/deck
  mw.connect(mw.mainWin.HanziStats, QtCore.SIGNAL('triggered()'), run00)
  mw.mainWin.menuTools.addAction(mw.mainWin.HanziStats)


####################################################################
#  Return all unique Hanzi in the current deck.                    #
####################################################################
def get_deckHanzi(SimpTrad=0,DeckSeen=0):
  # The following line determines which field is checked for hanzi. You can change the %Chinese% to something like %Hanzi% or whatever matches the field with Characters in.
  if SimpTrad == 1:
      hanzi_ids = mw.deck.s.column0("select id from fieldModels where name LIKE '%Trad%'")
  else:
      hanzi_ids = mw.deck.s.column0("select id from fieldModels where name LIKE '%Chinese%'")

  hanzis = ""
  hanzi = ""
  for hanzi_id in hanzi_ids:
    if DeckSeen == 0:
      hanzis = mw.deck.s.column0("select value from cards, fields where fieldModelID = :hid AND cards.factId = fields.factId AND cards.reps > 1", hid=hanzi_id)
    if DeckSeen == 1:
      hanzis = mw.deck.s.column0("select value from fields where fieldModelID = :hid", hid=hanzi_id)
    for u in hanzis:
      for c in u:
        if isKanji(c):
          if hanzi.find(c) == -1:
            hanzi = hanzi + c;
    
    # additionally get Hanzi from file
    if FILE:
      f = codecs.open(FILE, "rb", "utf8")
      for line in f.readlines():
        for c in line:
          if isKanji(c):
				    if hanzi.find(c) == -1:
					    hanzi = hanzi + c;
    
    
  return hanzi

####################################################################
#  Return all unique Hanzi from file.                              #
####################################################################
def get_fileHanzi(file):
  hanzis = ""
  hanzi = ""
  
  try:
    f = codecs.open(file, "rb", "utf8")
    for line in f.readlines():
      for c in line:
        if isKanji(c):
				  if hanzi.find(c) == -1:
					  hanzi = hanzi + c; 

    print "hanzi_stats", "read", file

  except:
    print "hanzi_stats", "error reading file", file
    
  return hanzi  

####################################################################
#  Return HTML formatted statistics on seen Hanzi in the frequent  #
#  Hanzi lists.                                                    #
####################################################################
def get_freqstats(SimpTrad,DeckSeen):
  hanzi = get_deckHanzi(SimpTrad,DeckSeen)
  # hanzi2 = get_fileHanzi(os.path.join(mw.config.configPath, "plugins", "known_hanzi.txt"))
  # hanzi = hanzi + hanzi2

  #  Create a map of the frequent Hanzi, in intervals of 500 characters.
  hanziMap = [
    {'hanzi': get_freqHanzi500()[SimpTrad],  'all_count': 500, 'seen_count': 0},
    {'hanzi': get_freqHanzi1000()[SimpTrad], 'all_count': 500, 'seen_count': 0},
    {'hanzi': get_freqHanzi1500()[SimpTrad], 'all_count': 500, 'seen_count': 0},
    {'hanzi': get_freqHanzi2000()[SimpTrad], 'all_count': 500, 'seen_count': 0},
    {'hanzi': get_freqHanzi2500()[SimpTrad], 'all_count': 500, 'seen_count': 0},
    {'hanzi': get_freqHanzi3000()[SimpTrad], 'all_count': 500, 'seen_count': 0},
    {'hanzi': get_freqHanzi3500()[SimpTrad], 'all_count': 500, 'seen_count': 0}
  ]

  # Count of all other Hanzi
  up3500 = 0

  #  For each group of frequent characters, count how many of the unique
  #  deck Hanzi are in each group.
  for k in hanzi:
    seen = 0
    for i in range(7):
      if k in hanziMap[i]['hanzi']:
        hanziMap[i]['seen_count'] += 1
        seen = 1
        continue
    if seen == 0:
      up3500 += 1

  #  Create a map with the actual statistics that will be used when showing
  #  the stats.
  sub_map = {}
  for i in range(7):
    sub_map['lvl' + str(i+1) + '_t'] = hanziMap[i]['all_count']
    sub_map['lvl' + str(i+1) + '_s'] = hanziMap[i]['seen_count']
    sub_map['lvl' + str(i+1) + '_p'] = round(hanziMap[i]['seen_count']*100.0 / hanziMap[i]['all_count'],2)

  #  Create the HTML formatted output.
  stats = """
		Character frequency data:<br>
    <table cellpadding=3>
    <tr><td><b>Freq chars</b></td><td><b>Seen</b></td><td><b>Seen %%</b></td></tr>
    <tr><td>1 - 500</td><td><a href=py:have500>%(lvl1_s)s</a> of <a href=py:missing500>%(lvl1_t)s</a></a></td><td>%(lvl1_p)s%%</td></tr>
    <tr><td>501 - 1000</td><td><a href=py:have1000>%(lvl2_s)s</a> of <a href=py:missing1000>%(lvl2_t)s</a></td><td>%(lvl2_p)s%%</td></tr>
    <tr><td>1001 - 1500</td><td><a href=py:have1500>%(lvl3_s)s</a> of <a href=py:missing1500>%(lvl3_t)s</a></td><td>%(lvl3_p)s%%</td></tr>
    <tr><td>1501 - 2000</td><td><a href=py:have2000>%(lvl4_s)s</a> of <a href=py:missing2000>%(lvl4_t)s</a></td><td>%(lvl4_p)s%%</td></tr>
    <tr><td>2001 - 2500</td><td><a href=py:have2500>%(lvl5_s)s</a> of <a href=py:missing2500>%(lvl5_t)s</a></td><td>%(lvl5_p)s%%</td></tr>
    <tr><td>2501 - 3000</td><td><a href=py:have3000>%(lvl6_s)s</a> of <a href=py:missing3000>%(lvl6_t)s</a></td><td>%(lvl6_p)s%%</td></tr>
    <tr><td>3001 - 3500</td><td><a href=py:have3500>%(lvl7_s)s</a> of <a href=py:missing3500>%(lvl7_t)s</a></td><td>%(lvl7_p)s%%</td></tr>
    <tr><td>3500++</td><td><a href=py:have3500up>""" % sub_map
  stats += str(up3500) + "</a></td><td></td></tr></table>"

  return stats

typeShow = "NONE"
whichStat = "NONE"

####################################################################
#  Return HTML formatted statistics on seen Hanzi in the 4 HSK     #
#  Hanzi lists.                                                    #
####################################################################
def get_hskstats(SimpTrad,DeckSeen):
  hanzi = get_deckHanzi(SimpTrad,DeckSeen)
  # hanzi2 = get_fileHanzi(os.path.join(mw.config.configPath, "plugins", "known_hanzi.txt"))
  # hanzi = hanzi + hanzi2

  #  Map of unique Hanzi in the different HSK levels
  hanziMap = [
    {'hanzi': get_hskB(), 'all_count':len(get_hskB()), 'seen_count': 0},
    {'hanzi': get_hskE(), 'all_count':len(get_hskE()), 'seen_count': 0},
    {'hanzi': get_hskI(), 'all_count':len(get_hskI()), 'seen_count': 0},
    {'hanzi': get_hskA(), 'all_count':len(get_hskA()), 'seen_count': 0}
  ]

  #  For each HSK level, count how many of the unique
  #  deck Hanzi are in each group.
  for k in hanzi:
    for i in range(4):
      if k in hanziMap[i]['hanzi']:
        hanziMap[i]['seen_count'] += 1
        continue

  #  Create a map with the actual statistics that will be used when showing
  #  the stats.
  sub_map = {}
  for i in range(4):
    sub_map['lvl' + str(i+1) + '_t'] = hanziMap[i]['all_count']
    sub_map['lvl' + str(i+1) + '_s'] = hanziMap[i]['seen_count']
    sub_map['lvl' + str(i+1) + '_p'] = round(hanziMap[i]['seen_count']*100.0 / hanziMap[i]['all_count'],2)

  #  Create the HTML formatted output.
  stats = """
    HSK statistics (characters, not words):
    <table cellpadding=3>
    <tr><td><b>HSK Level</b></td><td><b>Seen</b></td><td><b>Seen %%</b></td></tr>
    <tr><td>Basic (甲)</td><td><a href=py:haveB>%(lvl1_s)s</a> of <a href=py:missingB>%(lvl1_t)s</a></td><td>%(lvl1_p)s%%</td></tr>
    <tr><td>Elementary (乙)</td><td><a href=py:haveE>%(lvl2_s)s</a> of <a href=py:missingE>%(lvl2_t)s</a></td><td>%(lvl2_p)s%%</td></tr>
    <tr><td>Intermediate (丙)</td><td><a href=py:haveI>%(lvl3_s)s</a> of <a href=py:missingI>%(lvl3_t)s</a></td><td>%(lvl3_p)s%%</td></tr>
    <tr><td>Advanced (丁)</td><td><a href=py:haveA>%(lvl4_s)s</a> of <a href=py:missingA>%(lvl4_t)s</a></td><td>%(lvl4_p)s%%</td></tr>
    </table>
  """.decode("utf-8") % sub_map

  return stats

####################################################################
#  Return HTML formatted statistics on seen Hanzi in the 9 TW Grade Levels #
####################################################################
def get_twstats(SimpTrad,DeckSeen):
  hanzi = get_deckHanzi(SimpTrad,DeckSeen)
  # hanzi2 = get_fileHanzi(os.path.join(mw.config.configPath, "plugins", "known_hanzi.txt"))
  # hanzi = hanzi + hanzi2

  #  Map of unique Hanzi in the different TW  levels
  hanziMap = [
    {'hanzi': get_tw1(), 'all_count':len(get_tw1()), 'seen_count': 0},
    {'hanzi': get_tw2(), 'all_count':len(get_tw2()), 'seen_count': 0},
    {'hanzi': get_tw3(), 'all_count':len(get_tw3()), 'seen_count': 0},
    {'hanzi': get_tw4(), 'all_count':len(get_tw4()), 'seen_count': 0},
    {'hanzi': get_tw5(), 'all_count':len(get_tw5()), 'seen_count': 0},
    {'hanzi': get_tw6(), 'all_count':len(get_tw6()), 'seen_count': 0},
    {'hanzi': get_tw7(), 'all_count':len(get_tw7()), 'seen_count': 0},
    {'hanzi': get_tw8(), 'all_count':len(get_tw8()), 'seen_count': 0},
    {'hanzi': get_tw9(), 'all_count':len(get_tw9()), 'seen_count': 0}
  ]

  #  For each HSK level, count how many of the unique
  #  deck Hanzi are in each group.
  for k in hanzi:
    for i in range(9):
      if k in hanziMap[i]['hanzi']:
        hanziMap[i]['seen_count'] += 1
        continue

  #  Create a map with the actual statistics that will be used when showing
  #  the stats.
  sub_map = {}
  for i in range(9):
    sub_map['lvl' + str(i+1) + '_t'] = hanziMap[i]['all_count']
    sub_map['lvl' + str(i+1) + '_s'] = hanziMap[i]['seen_count']
    sub_map['lvl' + str(i+1) + '_p'] = round(hanziMap[i]['seen_count']*100.0 / hanziMap[i]['all_count'],2)

  sub_map['seen_or_deck'] = "Test"

  #  Create the HTML formatted output.
  desc = """Taiwan's Ministry of Education List <br> 常用國字標準字體表"""

  stats = """
    TW Ministry of Education List Statistics (characters):
    <table cellpadding=3>
    <tr><td><b>Grade</b></td><td><b>%(seen_or_deck)s</b></td><td><b>%(seen_or_deck)s %%</b></td></tr>
    <tr><td>第一級</td><td><a href=py:have_tw1>%(lvl1_s)s</a> of <a href=py:missing_tw1>%(lvl1_t)s</a></td><td>%(lvl1_p)s%%</td></tr>
    <tr><td>第二級</td><td><a href=py:have_tw2>%(lvl2_s)s</a> of <a href=py:missing_tw2>%(lvl2_t)s</a></td><td>%(lvl2_p)s%%</td></tr>
    <tr><td>第三級</td><td><a href=py:have_tw3>%(lvl3_s)s</a> of <a href=py:missing_tw3>%(lvl3_t)s</a></td><td>%(lvl3_p)s%%</td></tr>
    <tr><td>第四級</td><td><a href=py:have_tw4>%(lvl4_s)s</a> of <a href=py:missing_tw4>%(lvl4_t)s</a></td><td>%(lvl4_p)s%%</td></tr>
    <tr><td>第五級</td><td><a href=py:have_tw5>%(lvl5_s)s</a> of <a href=py:missing_tw5>%(lvl5_t)s</a></td><td>%(lvl5_p)s%%</td></tr>
    <tr><td>第六級</td><td><a href=py:have_tw6>%(lvl6_s)s</a> of <a href=py:missing_tw6>%(lvl6_t)s</a></td><td>%(lvl6_p)s%%</td></tr>
    <tr><td>第七級</td><td><a href=py:have_tw7>%(lvl7_s)s</a> of <a href=py:missing_tw7>%(lvl7_t)s</a></td><td>%(lvl7_p)s%%</td></tr>
    <tr><td>第八級</td><td><a href=py:have_tw8>%(lvl8_s)s</a> of <a href=py:missing_tw8>%(lvl8_t)s</a></td><td>%(lvl8_p)s%%</td></tr>
    <tr><td>第九級</td><td><a href=py:have_tw9>%(lvl9_s)s</a> of <a href=py:missing_tw9>%(lvl9_t)s</a></td><td>%(lvl9_p)s%%</td></tr>

    </table>
  """.decode("utf-8") % sub_map

  return stats




####################################################################
#  "Main" function, run when Hanzi statistics is clicked in the    #
#  Tool menu.                                                      #
####################################################################
def run00():
  slot_sync(0,0)

def run01():
  slot_sync(0,1)

def run10():
  slot_sync(1,0)

def run11():
  slot_sync(1,1)




def get_specificstats(SimpTrad, DeckSeen):
  if SimpTrad==0:
    return get_hskstats(SimpTrad,DeckSeen)
  if SimpTrad==1:
    return get_twstats(SimpTrad,DeckSeen)


def slot_sync(SimpTrad=0,DeckSeen=0):
  # Empty output
  OutText = ""

  # Set the prompt for new cards verus whole deck search
  if DeckSeen == 1:
    if SimpTrad == 0:
        seentype = "<b>Data Set</b>: <a href=py:run00>whole deck</a>"
    if SimpTrad == 1:
        seentype = "<b>Data Set</b>: <a href=py:run10>whole deck</a>"    
  else:
    if SimpTrad == 0:
        seentype = "<b>Data Set</b>: <a href=py:run01>seen cards only</a></small>"
    if SimpTrad == 1:
        seentype = "<b>Data Set</b>: <a href=py:run11>seen cards only</a></small>"
        
  #  Set the description for the search
  ctype = ""
  if SimpTrad ==0:
    if DeckSeen == 0:
      ctype = "<b>Character Set</b>: <a href=py:run10>Simplified</a>"
    else:
      ctype = "<b>Character Set</b>: <a href=py:run11>Simplified</a>"
  if SimpTrad == 1:
      if DeckSeen == 0:
        ctype = "<b>Character Set</b>: <a href=py:run00>Traditional</a>"
      else:
        ctype = "<b>Character Set</b>: <a href=py:run01>Traditional</a>"

    
  specificstats = get_specificstats(SimpTrad,DeckSeen)

  # Put the  html together from the above settings
  outText = """
      <h1>Hanzi Statistics (PyTK)</h1>
      <br>""" + ctype + """      
      <br>""" + seentype + """      
      <br>There are <b><u>""" + str(len(get_deckHanzi(SimpTrad,DeckSeen))) + """</b></u>
      unique Hanzi.<br><br> """ + specificstats + """ <br><br> """ + get_freqstats(SimpTrad,DeckSeen)

  mw.help.showText(outText, py={"missingB": onMhskB, 
                                                  "missingE": onMhskE, 
                                                  "missingI": onMhskI,
                                                  "missingA": onMhskA, 
                                                  "haveB": onHhskB, 
                                                  "haveE": onHhskE, 
                                                  "haveI": onHhskI, 
                                                  "haveA": onHhskA,
                                                  "missing_tw1": onMtw1, 
                                                  "missing_tw2": onMtw2,                                                   
                                                  "missing_tw3": onMtw3,
                                                  "missing_tw4": onMtw4, 
                                                  "missing_tw5": onMtw5, 
                                                  "missing_tw6": onMtw6, 
                                                  "missing_tw7": onMtw7, 
                                                  "missing_tw8": onMtw8, 
                                                  "missing_tw9": onMtw9, 
                                                  "have_tw1": onHtw1, 
                                                  "have_tw2": onHtw2, 
                                                  "have_tw3": onHtw3, 
                                                  "have_tw4": onHtw4, 
                                                  "have_tw5": onHtw5, 
                                                  "have_tw6": onHtw6, 
                                                  "have_tw7": onHtw7, 
                                                  "have_tw8": onHtw8, 
                                                  "have_tw9": onHtw9, 
                                                  "missing500": onMFreq500, 
                                                  "missing1000": onMFreq1000, 
                                                  "missing1500": onMFreq1500, 
                                                  "missing2000": onMFreq2000,
                                                  "missing2500": onMFreq2500, 
                                                  "missing3000": onMFreq3000, 
                                                  "missing3500": onMFreq3500, 
                                                  "have500": onHFreq500,
                                                  "have1000": onHFreq1000, 
                                                  "have1500": onHFreq1500, 
                                                  "have2000": onHFreq2000, 
                                                  "have2500": onHFreq2500,
                                                  "have3000": onHFreq3000, 
                                                  "have3500": onHFreq3500, 
                                                  "have3500up": onHFreq3500up,
                                                  "run00": run00,
                                                  "run01": run01,
                                                  "run10": run10,
                                                  "run11": run11
                                                   })


def backLink():
  return "<a href=py:back>Go back</a>"

####################################################################
#  Return HTML formatted statistics on seen Hanzi in the 4 TOP     #
#  Hanzi lists.                                                    #
####################################################################
def get_topstats(SimpTrad,DeckSeen):
  hanzi = get_deckHanzi(SimpTrad,DeckSeen)
  # hanzi2 = get_fileHanzi(os.path.join(mw.config.configPath, "plugins", "known_hanzi.txt"))
  # hanzi = hanzi + hanzi2

  #  Map of unique Hanzi in the different HSK levels
  hanziMap = [
    {'hanzi': get_top1(), 'all_count':len(get_top1()), 'seen_count': 0},
    {'hanzi': get_top2(), 'all_count':len(get_top2()), 'seen_count': 0},
    {'hanzi': get_top3(), 'all_count':len(get_top3()), 'seen_count': 0},
    {'hanzi': get_top4(), 'all_count':len(get_top4()), 'seen_count': 0}
  ]

  #  For each TOP level, count how many of the unique
  #  deck Hanzi are in each group.
  for k in hanzi:
    for i in range(4):
      if k in hanziMap[i]['hanzi']:
        hanziMap[i]['seen_count'] += 1
        continue

  #  Create a map with the actual statistics that will be used when showing
  #  the stats.
  sub_map = {}
  for i in range(4):
    sub_map['lvl' + str(i+1) + '_t'] = hanziMap[i]['all_count']
    sub_map['lvl' + str(i+1) + '_s'] = hanziMap[i]['seen_count']
    sub_map['lvl' + str(i+1) + '_p'] = round(hanziMap[i]['seen_count']*100.0 / hanziMap[i]['all_count'],2)

  sub_map['seen_or_deck'] = SEENDECKTXT

  #  Create the HTML formatted output.
  desc = """TOP Test Of Proficiency-Huayu <br> 華語文能力測驗"""

  stats = """
    TOP Statistics (characters):
    <table cellpadding=3>
    <tr><td><b>TOP Level</b></td><td><b>%(seen_or_deck)s</b></td><td><b>%(seen_or_deck)s %%</b></td></tr>
    <tr><td>Basic (基礎)</td><td><a href=py:haveB>%(lvl1_s)s</a> of <a href=py:missingB>%(lvl1_t)s</a></td><td>%(lvl1_p)s%%</td></tr>
    <tr><td>Elementary (初等)</td><td><a href=py:haveE>%(lvl2_s)s</a> of <a href=py:missingE>%(lvl2_t)s</a></td><td>%(lvl2_p)s%%</td></tr>
    <tr><td>Intermediate (中等)</td><td><a href=py:haveI>%(lvl3_s)s</a> of <a href=py:missingI>%(lvl3_t)s</a></td><td>%(lvl3_p)s%%</td></tr>
    <tr><td>Advanced (高等)</td><td><a href=py:haveA>%(lvl4_s)s</a> of <a href=py:missingA>%(lvl4_t)s</a></td><td>%(lvl4_p)s%%</td></tr>
    </table>
  """.decode("utf-8") % sub_map

  return stats

####################################################################
#  Show missing or seen Hanzi.                                     #
####################################################################
def onShowHanzi(base, choice, SimpTrad, DeckSeen):
  out = ""
  if choice == "missing": out += "<h1>Missing Hanzi</h1>"
  if choice == "have": out += "<h1>Seen Hanzi</h1>"
  if choice == "other": out += "<h1>Other Hanzi</h1>"
  out += backLink() + "<br><br>"
  missing = ""
  hanzi = get_deckHanzi(SimpTrad,DeckSeen)
  if choice == "other":
    for h in hanzi:
      if h not in base:
        missing += h
        continue
  else:
    for h in base:
      if choice == "missing":
        if h not in hanzi:
          missing += h
          continue
      if choice == "have":
        if h in hanzi:
          missing += h
          continue
  out += '<font size=12 face="SimSun"><b>'
  for h in missing:
    out += '<a href="http://www.mdbg.net/chindict/chindict.php?page=worddictbasic&wdqb=' + h + '&wdrst=0&wdeac=1">' + h + '</a>'
  out += "</b></font>"
  
def onMhskB(): onShowHanzi(get_hskB(), "missing",0,1)
def onMhskE(): onShowHanzi(get_hskE(), "missing",0,1)
def onMhskI(): onShowHanzi(get_hskI(), "missing",0,1)
def onMhskA(): onShowHanzi(get_hskA(), "missing",0,1)

def onHhskB(): onShowHanzi(get_hskB(), "have",0,1)
def onHhskE(): onShowHanzi(get_hskE(), "have",0,1)
def onHhskI(): onShowHanzi(get_hskI(), "have",0,1)
def onHhskA(): onShowHanzi(get_hskA(), "have",0,1)

def onMtw1(): onShowHanzi(get_tw1(), "missing",1,1)
def onMtw2(): onShowHanzi(get_tw2(), "missing",1,1)
def onMtw3(): onShowHanzi(get_tw3(), "missing",1,1)
def onMtw4(): onShowHanzi(get_tw4(), "missing",1,1)
def onMtw5(): onShowHanzi(get_tw5(), "missing",1,1)
def onMtw6(): onShowHanzi(get_tw6(), "missing",1,1)
def onMtw7(): onShowHanzi(get_tw7(), "missing",1,1)
def onMtw8(): onShowHanzi(get_tw8(), "missing",1,1)
def onMtw9(): onShowHanzi(get_tw9(), "missing",1,1)

def onHtw1(): onShowHanzi(get_tw1(), "have",1,1)
def onHtw2(): onShowHanzi(get_tw2(), "have",1,1)
def onHtw3(): onShowHanzi(get_tw3(), "have",1,1)
def onHtw4(): onShowHanzi(get_tw4(), "have",1,1)
def onHtw5(): onShowHanzi(get_tw5(), "have",1,1)
def onHtw6(): onShowHanzi(get_tw6(), "have",1,1)
def onHtw7(): onShowHanzi(get_tw7(), "have",1,1)
def onHtw8(): onShowHanzi(get_tw8(), "have",1,1)
def onHtw9(): onShowHanzi(get_tw9(), "have",1,1)

def onMFreq500(): onShowHanzi(get_freqHanzi500()[SimpTrad], "missing")
def onMFreq1000(): onShowHanzi(get_freqHanzi1000()[SimpTrad], "missing")
def onMFreq1500(): onShowHanzi(get_freqHanzi1500()[SimpTrad], "missing")
def onMFreq2000(): onShowHanzi(get_freqHanzi2000()[SimpTrad], "missing")
def onMFreq2500(): onShowHanzi(get_freqHanzi2500()[SimpTrad], "missing")
def onMFreq3000(): onShowHanzi(get_freqHanzi3000()[SimpTrad], "missing")
def onMFreq3500(): onShowHanzi(get_freqHanzi3500()[SimpTrad], "missing")

def onHFreq500(): onShowHanzi(get_freqHanzi500()[SimpTrad], "have")
def onHFreq1000(): onShowHanzi(get_freqHanzi1000()[SimpTrad], "have")
def onHFreq1500(): onShowHanzi(get_freqHanzi1500()[SimpTrad], "have")
def onHFreq2000(): onShowHanzi(get_freqHanzi2000()[SimpTrad], "have")
def onHFreq2500(): onShowHanzi(get_freqHanzi2500()[SimpTrad], "have")
def onHFreq3000(): onShowHanzi(get_freqHanzi3000()[SimpTrad], "have")
def onHFreq3500(): onShowHanzi(get_freqHanzi3500()[SimpTrad], "have")
def onHFreq3500up(): onShowHanzi(get_freqHanzi500()[SimpTrad] + get_freqHanzi1000()[SimpTrad] + get_freqHanzi1500()[SimpTrad] + get_freqHanzi2000()[SimpTrad] + get_freqHanzi2500()[SimpTrad] + get_freqHanzi3000()[SimpTrad] + get_freqHanzi3500()[SimpTrad], "other")

def get_freqHanzi500():
  return ['的一是不了在人有我他这个们中来上大为和国地到以说时要就出会可也你对生能而子那得于着下自之年过发后作里用道行所然家种事成方多经么去法学如都同现当没动面起看定天分还进好小部其些主样理心她本前开但因只从想实日军者意无力它与长把机十民第公此已工使情明性知全三又关点正业外将两高间由问很最重并物手应战向头文体政美相见被利什二等产或新己制身果加西斯月话合回特代内信表化老给世位次度门任常先海通教儿原东声提立及比员解水名真论处走义各入几口认条平系气题活尔更别打女变四神总何电数安少报才结反受目太量再感建务做接必场件计管期市直德资命山金指克许统区保至队形社便空决治展马科司五基眼书非则听白却界达光放强即像难且权思王象完设式色路记南品住告类求据程北边死张该交规万取拉格望觉术领共确传师观清今切院让识候带导争运笑飞风步改收根干造言联持组每济车亲极林服快办议往元英士证近失转夫令准布始怎呢存未远叫台单影具罗字爱击流备兵连调深商算质团集百需价花党华城石级整府离况亚请技际约示复病息究线似官火断精满支视消越器容照须九增研写称企八功吗包片史委乎查轻易早曾除农找装广显吧阿李标谈吃图念六引历首医局突专费号尽另周较注语仅考落青随选列'.decode("utf-8"),
       '的一是不了在人有我他這個們中來上大為和國地到以說時要就出會可也你對生能而子那得於著下自之年過發后作裡用道行所然家種事成方多經麼去法學如都同現當沒動面起看定天分還進好小部其些主樣理心她本前開但因隻從想實日軍者意無力它與長把機十民第公此已工使情明性知全三又關點正業外將兩高間由問很最重並物手應戰向頭文體政美相見被利什二等產或新己制身果加西斯月話合回特代內信表化老給世位次度門任常先海通教兒原東聲提立及比員解水名真論處走義各入幾口認條平系氣題活爾更別打女變四神總何電數安少報才結反受目太量再感建務做接必場件計管期市直德資命山金指克許統區保至隊形社便空決治展馬科司五基眼書非則聽白卻界達光放強即像難且權思王象完設式色路記南品住告類求據程北邊死張該交規萬取拉格望覺術領共確傳師觀清今切院讓識候帶導爭運笑飛風步改收根干造言聯持組每濟車親極林服快辦議往元英士証近失轉夫令准布始怎呢存未遠叫台單影具羅字愛擊流備兵連調深商算質團集百需價花黨華城石級整府離況亞請技際約示復病息究線似官火斷精滿支視消越器容照須九增研寫稱企八功嗎包片史委乎查輕易早曾除農找裝廣顯吧阿李標談吃圖念六引歷首醫局突專費號盡另周較注語僅考落青隨選列'.decode("utf-8")]

def get_freqHanzi1000():
  return ['武红响虽推势参希古众构房半节土投某案黑维革划敌致陈律足态护七兴派孩验责营星够章音跟志底站严巴例防族供效续施留讲型料终答紧黄绝奇察母京段依批群项故按河米围江织害斗双境客纪采举杀攻父苏密低朝友诉止细愿千值仍男钱破网热助倒育属坐帝限船脸职速刻乐否刚威毛状率甚独球般普怕弹校苦创假久错承印晚兰试股拿脑预谁益阳若哪微尼继送急血惊伤素药适波夜省初喜卫源食险待述陆习置居劳财环排福纳欢雷警获模充负云停木游龙树疑层冷洲冲射略范竟句室异激汉村哈策演简卡罪判担州静退既衣您宗积余痛检差富灵协角占配征修皮挥胜降阶审沉坚善妈刘读啊超免压银买皇养伊怀执副乱抗犯追帮宣佛岁航优怪香著田铁控税左右份穿艺背阵草脚概恶块顿敢守酒岛托央户烈洋哥索胡款靠评版宝座释景顾弟登货互付伯慢欧换闻危忙核暗姐介坏讨丽良序升监临亮露永呼味野架域沙掉括舰鱼杂误湾吉减编楚肯测败屋跑梦散温困剑渐封救贵枪缺楼县尚毫移娘朋画班智亦耳恩短掌恐遗固席松秘谢鲁遇康虑幸均销钟诗藏赶剧票损忽巨炮旧端探湖录叶春乡附吸予礼港雨呀板庭妇归睛饭额含顺输摇招婚脱补谓督毒油疗旅泽材灭逐莫笔亡鲜词圣择寻厂睡博勒烟授诺伦岸奥唐卖俄炸载洛健堂旁宫喝借君禁阴园谋宋避抓荣姑孙逃牙束跳顶'.decode("utf-8"),
          '武紅響雖推勢參希古眾構房半節土投某案黑維革劃敵致陳律足態護七興派孩驗責營星夠章音跟志底站嚴巴例防族供效續施留講型料終答緊黃絕奇察母京段依批群項故按河米圍江織害斗雙境客紀採舉殺攻父蘇密低朝友訴止細願千值仍男錢破網熱助倒育屬坐帝限船臉職速刻樂否剛威毛狀率甚獨球般普怕彈校苦創假久錯承印晚蘭試股拿腦預誰益陽若哪微尼繼送急血驚傷素藥適波夜省初喜衛源食險待述陸習置居勞財環排福納歡雷警獲模充負雲停木游龍樹疑層冷洲沖射略范竟句室異激漢村哈策演簡卡罪判擔州靜退既衣您宗積余痛檢差富靈協角佔配征修皮揮勝降階審沉堅善媽劉讀啊超免壓銀買皇養伊懷執副亂抗犯追幫宣佛歲航優怪香著田鐵控稅左右份穿藝背陣草腳概惡塊頓敢守酒島托央戶烈洋哥索胡款靠評版寶座釋景顧弟登貨互付伯慢歐換聞危忙核暗姐介壞討麗良序升監臨亮露永呼味野架域沙掉括艦魚雜誤灣吉減編楚肯測敗屋跑夢散溫困劍漸封救貴槍缺樓縣尚毫移娘朋畫班智亦耳恩短掌恐遺固席鬆秘謝魯遇康慮幸均銷鐘詩藏趕劇票損忽巨炮舊端探湖錄葉春鄉附吸予禮港雨呀板庭婦歸睛飯額含順輸搖招婚脫補謂督毒油療旅澤材滅逐莫筆亡鮮詞聖擇尋廠睡博勒煙授諾倫岸奧唐賣俄炸載洛健堂旁宮喝借君禁陰園謀宋避抓榮姑孫逃牙束跳頂'.decode("utf-8")]

def get_freqHanzi1500():
  return ['玉镇雪午练迫爷篇肉嘴馆遍凡础洞卷坦牛宁纸诸训私庄祖丝翻暴森塔默握戏隐熟骨访弱蒙歌店鬼软典欲萨伙遭盘爸扩盖弄雄稳忘亿刺拥徒姆杨齐赛趣曲刀床迎冰虚玩析窗醒妻透购替塞努休虎扬途侵刑绿兄迅套贸毕唯谷轮库迹尤竞街促延震弃甲伟麻川申缓潜闪售灯针哲络抵朱埃抱鼓植纯夏忍页杰筑折郑贝尊吴秀混臣雅振染盛怒舞圆搞狂措姓残秋培迷诚宽宇猛摆梅毁伸摩盟末乃悲拍丁赵硬麦蒋操耶阻订彩抽赞魔纷沿喊违妹浪汇币丰蓝殊献桌啦瓦莱援译夺汽烧距裁偏符勇触课敬哭懂墙袭召罚侠厅拜巧侧韩冒债曼融惯享戴童犹乘挂奖绍厚纵障讯涉彻刊丈爆乌役描洗玛患妙镜唱烦签仙彼弗症仿倾牌陷鸟轰咱菜闭奋庆撤泪茶疾缘播朗杜奶季丹狗尾仪偷奔珠虫驻孔宜艾桥淡翼恨繁寒伴叹旦愈潮粮缩罢聚径恰挑袋灰捕徐珍幕映裂泰隔启尖忠累炎暂估泛荒偿横拒瑞忆孤鼻闹羊呆厉衡胞零穷舍码赫婆魂灾洪腿胆津俗辩胸晓劲贫仁偶辑邦恢赖圈摸仰润堆碰艇稍迟辆废净凶署壁御奉旋冬矿抬蛋晨伏吹鸡倍糊秦盾杯租骑乏隆诊奴摄丧污渡旗甘耐凭扎抢绪粗肩梁幻菲皆碎宙叔岩荡综爬荷悉蒂返井壮薄悄扫敏碍殖详迪矛霍允幅撒剩凯颗骂赏液番箱贴漫酸郎腰舒眉忧浮辛恋餐吓挺励辞艘键伍峰尺昨黎辈贯侦滑券崇扰宪绕趋慈乔阅汗枝拖墨胁插箭腊粉泥氏'.decode("utf-8"),
          '玉鎮雪午練迫爺篇肉嘴館遍凡礎洞卷坦牛寧紙諸訓私庄祖絲翻暴森塔默握戲隱熟骨訪弱蒙歌店鬼軟典欲薩伙遭盤爸擴蓋弄雄穩忘億刺擁徒姆楊齊賽趣曲刀床迎冰虛玩析窗醒妻透購替塞努休虎揚途侵刑綠兄迅套貿畢唯谷輪庫跡尤競街促延震棄甲偉麻川申緩潛閃售燈針哲絡抵朱埃抱鼓植純夏忍頁杰筑折鄭貝尊吳秀混臣雅振染盛怒舞圓搞狂措姓殘秋培迷誠寬宇猛擺梅毀伸摩盟末乃悲拍丁趙硬麥蔣操耶阻訂彩抽贊魔紛沿喊違妹浪匯幣豐藍殊獻桌啦瓦萊援譯奪汽燒距裁偏符勇觸課敬哭懂牆襲召罰俠廳拜巧側韓冒債曼融慣享戴童猶乘挂獎紹厚縱障訊涉徹刊丈爆烏役描洗瑪患妙鏡唱煩簽仙彼弗症仿傾牌陷鳥轟咱菜閉奮慶撤淚茶疾緣播朗杜奶季丹狗尾儀偷奔珠虫駐孔宜艾橋淡翼恨繁寒伴嘆旦愈潮糧縮罷聚徑恰挑袋灰捕徐珍幕映裂泰隔啟尖忠累炎暫估泛荒償橫拒瑞憶孤鼻鬧羊呆厲衡胞零窮舍碼赫婆魂災洪腿膽津俗辯胸曉勁貧仁偶輯邦恢賴圈摸仰潤堆碰艇稍遲輛廢淨凶署壁御奉旋冬礦抬蛋晨伏吹雞倍糊秦盾杯租騎乏隆診奴攝喪污渡旗甘耐憑扎搶緒粗肩梁幻菲皆碎宙叔岩蕩綜爬荷悉蒂返井壯薄悄掃敏礙殖詳迪矛霍允幅撒剩凱顆罵賞液番箱貼漫酸郎腰舒眉憂浮辛戀餐嚇挺勵辭艘鍵伍峰尺昨黎輩貫偵滑券崇擾憲繞趨慈喬閱汗枝拖墨脅插箭臘粉泥氏'.decode("utf-8")]

def get_freqHanzi2000():
  return ['彭拔骗凤慧媒佩愤扑龄驱惜豪掩兼跃尸肃帕驶堡届欣惠册储飘桑闲惨洁踪勃宾频仇磨递邪撞拟滚奏巡颜剂绩贡疯坡瞧截燃焦殿伪柳锁逼颇昏劝呈搜勤戒驾漂饮曹朵仔柔俩孟腐幼践籍牧凉牲佳娜浓芳稿竹腹跌逻垂遵脉貌柏狱猜怜惑陶兽帐饰贷昌叙躺钢沟寄扶铺邓寿惧询汤盗肥尝匆辉奈扣廷澳嘛董迁凝慰厌脏腾幽怨鞋丢埋泉涌辖躲晋紫艰魏吾慌祝邮吐狠鉴曰械咬邻赤挤弯椅陪割揭韦悟聪雾锋梯猫祥阔誉筹丛牵鸣沈阁穆屈旨袖猎臂蛇贺柱抛鼠瑟戈牢逊迈欺吨琴衰瓶恼燕仲诱狼池疼卢仗冠粒遥吕玄尘冯抚浅敦纠钻晶岂峡苍喷耗凌敲菌赔涂粹扁亏寂煤熊恭湿循暖糖赋抑秩帽哀宿踏烂袁侯抖夹昆肝擦猪炼恒慎搬纽纹玻渔磁铜齿跨押怖漠疲叛遣兹祭醉拳弥斜档稀捷肤疫肿豆削岗晃吞宏癌肚隶履涨耀扭坛拨沃绘伐堪仆郭牺歼墓雇廉契拼惩捉覆刷劫嫌瓜歇雕闷乳串娃缴唤赢莲霸桃妥瘦搭赴岳嘉舱俊址庞耕锐缝悔邀玲惟斥宅添挖呵讼氧浩羽斤酷掠妖祸侍乙妨贪挣汪尿莉悬唇翰仓轨枚盐览傅帅庙芬屏寺胖璃愚滴疏萧姿颤丑劣柯寸扔盯辱匹俱辨饿蜂哦腔郁溃谨糟葛苗肠忌溜鸿爵鹏鹰笼丘桂滋聊挡纲肌茨壳痕碗穴膀卓贤卧膜毅锦欠哩函茫昂薛皱夸豫胃舌剥傲拾窝睁携陵哼棉晴铃填饲渴吻扮逆脆喘罩卜炉柴愉绳胎蓄眠竭喂傻慕浑奸扇柜悦拦诞饱乾泡'.decode("utf-8"),
          '彭拔騙鳳慧媒佩憤扑齡驅惜豪掩兼躍尸肅帕駛堡屆欣惠冊儲飄桑閑慘潔蹤勃賓頻仇磨遞邪撞擬滾奏巡顏劑績貢瘋坡瞧截燃焦殿偽柳鎖逼頗昏勸呈搜勤戒駕漂飲曹朵仔柔倆孟腐幼踐籍牧涼牲佳娜濃芳稿竹腹跌邏垂遵脈貌柏獄猜憐惑陶獸帳飾貸昌敘躺鋼溝寄扶鋪鄧壽懼詢湯盜肥嘗匆輝奈扣廷澳嘛董遷凝慰厭臟騰幽怨鞋丟埋泉涌轄躲晉紫艱魏吾慌祝郵吐狠鑒曰械咬鄰赤擠彎椅陪割揭韋悟聰霧鋒梯貓祥闊譽籌叢牽鳴沈閣穆屈旨袖獵臂蛇賀柱拋鼠瑟戈牢遜邁欺噸琴衰瓶惱燕仲誘狼池疼盧仗冠粒遙呂玄塵馮撫淺敦糾鑽晶豈峽蒼噴耗凌敲菌賠涂粹扁虧寂煤熊恭濕循暖糖賦抑秩帽哀宿踏爛袁侯抖夾昆肝擦豬煉恆慎搬紐紋玻漁磁銅齒跨押怖漠疲叛遣茲祭醉拳彌斜檔稀捷膚疫腫豆削崗晃吞宏癌肚隸履漲耀扭壇撥沃繪伐堪仆郭犧殲墓雇廉契拼懲捉覆刷劫嫌瓜歇雕悶乳串娃繳喚贏蓮霸桃妥瘦搭赴岳嘉艙俊址龐耕銳縫悔邀玲惟斥宅添挖呵訟氧浩羽斤酷掠妖禍侍乙妨貪掙汪尿莉懸唇翰倉軌枚鹽覽傅帥廟芬屏寺胖璃愚滴疏蕭姿顫丑劣柯寸扔盯辱匹俱辨餓蜂哦腔郁潰謹糟葛苗腸忌溜鴻爵鵬鷹籠丘桂滋聊擋綱肌茨殼痕碗穴膀卓賢臥膜毅錦欠哩函茫昂薛皺夸豫胃舌剝傲拾窩睜攜陵哼棉晴鈴填飼渴吻扮逆脆喘罩卜爐柴愉繩胎蓄眠竭喂傻慕渾奸扇櫃悅攔誕飽乾泡'.decode("utf-8")]

def get_freqHanzi2500():
  return ['贼亭夕爹酬儒姻卵氛泄杆挨僧蜜吟猩遂狭肖甜霞驳裕顽於摘矮秒卿畜咽披辅勾盆疆赌塑畏吵囊嗯泊肺骤缠冈羞瞪吊贾漏斑涛悠鹿俘锡卑葬铭滩嫁催璇翅盒蛮矣潘歧赐鲍锅廊拆灌勉盲宰佐啥胀扯禧辽抹筒棋裤唉朴咐孕誓喉妄拘链驰栏逝窃艳臭纤玑棵趁匠盈翁愁瞬婴孝颈倘浙谅蔽畅赠妮莎尉冻跪闯葡後厨鸭颠遮谊圳吁仑辟瘤嫂陀框谭亨钦庸歉芝吼甫衫摊宴嘱衷娇陕矩浦讶耸裸碧摧薪淋耻胶屠鹅饥盼脖虹翠崩账萍逢赚撑翔倡绵猴枯巫昭怔渊凑溪蠢禅阐旺寓藤匪伞碑挪琼脂谎慨菩萄狮掘抄岭晕逮砍掏狄晰罕挽脾舟痴蔡剪脊弓懒叉拐喃僚捐姊骚拓歪粘柄坑陌窄湘兆崖骄刹鞭芒筋聘钩棍嚷腺弦焰耍俯厘愣厦恳饶钉寡憾摔叠惹喻谱愧煌徽溶坠煞巾滥洒堵瓷咒姨棒郡浴媚稣淮哎屁漆淫巢吩撰啸滞玫硕钓蝶膝姚茂躯吏猿寨恕渠戚辰舶颁惶狐讽笨袍嘲啡泼衔倦涵雀旬僵撕肢垄夷逸茅侨舆窑涅蒲谦杭噢弊勋刮郊凄捧浸砖鼎篮蒸饼亩肾陡爪兔殷贞荐哑炭坟眨搏咳拢舅昧擅爽咖搁禄雌哨巩绢螺裹昔轩谬谍龟媳姜瞎冤鸦蓬巷琳栽沾诈斋瞒彪厄咨纺罐桶壤糕颂膨谐垒咕隙辣绑宠嘿兑霉挫稽辐乞纱裙嘻哇绣杖塘衍轴攀膊譬斌祈踢肆坎轿棚泣屡躁邱凰溢椎砸趟帘帆栖窜丸斩堤塌贩厢掀喀乖谜捏阎滨虏匙芦苹卸沼钥株祷剖熙哗劈怯棠胳桩瑰娱娶沫嗓蹲焚淘嫩'.decode("utf-8"),
          '賊亭夕爹酬儒姻卵氛泄杆挨僧蜜吟猩遂狹肖甜霞駁裕頑於摘矮秒卿畜咽披輔勾盆疆賭塑畏吵囊嗯泊肺驟纏岡羞瞪吊賈漏斑濤悠鹿俘錫卑葬銘灘嫁催璇翅盒蠻矣潘歧賜鮑鍋廊拆灌勉盲宰佐啥脹扯禧遼抹筒棋褲唉朴咐孕誓喉妄拘鏈馳欄逝竊艷臭纖璣棵趁匠盈翁愁瞬嬰孝頸倘浙諒蔽暢贈妮莎尉凍跪闖葡後廚鴨顛遮誼圳吁侖辟瘤嫂陀框譚亨欽庸歉芝吼甫衫攤宴囑衷嬌陝矩浦訝聳裸碧摧薪淋恥膠屠鵝飢盼脖虹翠崩賬萍逢賺撐翔倡綿猴枯巫昭怔淵湊溪蠢禪闡旺寓藤匪傘碑挪瓊脂謊慨菩萄獅掘抄嶺暈逮砍掏狄晰罕挽脾舟痴蔡剪脊弓懶叉拐喃僚捐姊騷拓歪粘柄坑陌窄湘兆崖驕剎鞭芒筋聘鉤棍嚷腺弦焰耍俯厘愣廈懇饒釘寡憾摔疊惹喻譜愧煌徽溶墜煞巾濫洒堵瓷咒姨棒郡浴媚穌淮哎屁漆淫巢吩撰嘯滯玫碩釣蝶膝姚茂軀吏猿寨恕渠戚辰舶頒惶狐諷笨袍嘲啡潑銜倦涵雀旬僵撕肢壟夷逸茅僑輿窯涅蒲謙杭噢弊勛刮郊淒捧浸磚鼎籃蒸餅畝腎陡爪兔殷貞薦啞炭墳眨搏咳攏舅昧擅爽咖擱祿雌哨鞏絹螺裹昔軒謬諜龜媳姜瞎冤鴉蓬巷琳栽沾詐齋瞞彪厄咨紡罐桶壤糕頌膨諧壘咕隙辣綁寵嘿兌霉挫稽輻乞紗裙嘻哇繡杖塘衍軸攀膊譬斌祈踢肆坎轎棚泣屢躁邱凰溢椎砸趟帘帆棲竄丸斬堤塌販廂掀喀乖謎捏閻濱虜匙蘆蘋卸沼鑰株禱剖熙嘩劈怯棠胳樁瑰娛娶沫嗓蹲焚淘嫩'.decode("utf-8")]

def get_freqHanzi3000():
  return ['韵衬匈钧竖峻豹捞菊鄙魄兜哄颖镑屑蚁壶怡渗秃迦旱哟咸焉谴宛稻铸锻伽詹毙恍贬烛骇芯汁桓坊驴朽靖佣汝碌迄冀荆崔雁绅珊榜诵傍彦醇笛禽勿娟瞄幢寇睹贿踩霆呜拱妃蔑谕缚诡篷淹腕煮倩卒勘馨逗甸贱炒灿敞蜡囚栗辜垫妒魁谣寞蜀甩涯枕丐泳奎泌逾叮黛燥掷藉枢憎鲸弘倚侮藩拂鹤蚀浆芙垃烤晒霜剿蕴圾绸屿氢驼妆捆铅逛淑榴丙痒钞蹄犬躬昼藻蛛褐颊奠募耽蹈陋侣魅岚侄虐堕陛莹荫狡阀绞膏垮茎缅喇绒搅凳梭丫姬诏钮棺耿缔懈嫉灶匀嗣鸽澡凿纬沸畴刃遏烁嗅叭熬瞥骸奢拙栋毯桐砂莽泻坪梳杉晤稚蔬蝇捣顷麽尴镖诧尬硫嚼羡沦沪旷彬芽狸冥碳咧惕暑咯萝汹腥窥俺潭崎麟捡拯厥澄萎哉涡滔暇溯鳞酿茵愕瞅暮衙诫斧兮焕棕佑嘶妓喧蓉删樱伺嗡娥梢坝蚕敷澜杏绥冶庇挠搂倏聂婉噪稼鳍菱盏匿吱寝揽髓秉哺矢啪帜邵嗽挟缸揉腻驯缆晌瘫贮觅朦僻隋蔓咋嵌虔畔琐碟涩胧嘟蹦冢浏裔襟叨诀旭虾簿啤擒枣嘎苑牟呕骆凸熄兀喔裳凹赎屯膛浇灼裘砰棘橡碱聋姥瑜毋娅沮萌俏黯撇粟粪尹苟癫蚂禹廖俭帖煎缕窦簇棱叩呐瑶墅莺烫蛙歹伶葱哮眩坤廓讳啼乍瓣矫跋枉梗厕琢讥釉窟敛轼庐胚呻绰扼懿炯竿慷虞锤栓桨蚊磅孽惭戳禀鄂馈垣溅咚钙礁彰豁眯磷雯墟迂瞻颅琉悼蝴拣渺眷悯汰慑婶斐嘘镶炕宦趴绷窘襄珀嚣拚酌浊毓撼嗜扛峭磕翘槽淌栅颓熏瑛颐忖'.decode("utf-8"),
          '韻襯匈鈞豎峻豹撈菊鄙魄兜哄穎鎊屑蟻壺怡滲禿迦旱喲咸焉譴宛稻鑄鍛伽詹斃恍貶燭駭芯汁桓坊驢朽靖佣汝碌迄冀荊崔雁紳珊榜誦傍彥醇笛禽勿娟瞄幢寇睹賄踩霆嗚拱妃蔑諭縛詭篷淹腕煮倩卒勘馨逗甸賤炒燦敞蠟囚栗辜墊妒魁謠寞蜀甩涯枕丐泳奎泌逾叮黛燥擲藉樞憎鯨弘倚侮藩拂鶴蝕漿芙垃烤晒霜剿蘊圾綢嶼氫駝妝捆鉛逛淑榴丙痒鈔蹄犬躬晝藻蛛褐頰奠募耽蹈陋侶魅嵐侄虐墮陛瑩蔭狡閥絞膏垮莖緬喇絨攪凳梭丫姬詔鈕棺耿締懈嫉灶勻嗣鴿澡鑿緯沸疇刃遏爍嗅叭熬瞥骸奢拙棟毯桐砂莽瀉坪梳杉晤稚蔬蠅搗頃麼尷鏢詫尬硫嚼羨淪滬曠彬芽狸冥碳咧惕暑咯蘿洶腥窺俺潭崎麟撿拯厥澄萎哉渦滔暇溯鱗釀茵愕瞅暮衙誡斧兮煥棕佑嘶妓喧蓉刪櫻伺嗡娥梢壩蠶敷瀾杏綏冶庇撓摟倏聶婉噪稼鰭菱盞匿吱寢攬髓秉哺矢啪幟邵嗽挾缸揉膩馴纜晌癱貯覓朦僻隋蔓咋嵌虔畔瑣碟澀朧嘟蹦塚瀏裔襟叨訣旭蝦簿啤擒棗嘎苑牟嘔駱凸熄兀喔裳凹贖屯膛澆灼裘砰棘橡鹼聾姥瑜毋婭沮萌俏黯撇粟糞尹苟癲螞禹廖儉帖煎縷竇簇棱叩吶瑤墅鶯燙蛙歹伶蔥哮眩坤廓諱啼乍瓣矯跋枉梗廁琢譏釉窟斂軾廬胚呻綽扼懿炯竿慷虞錘栓槳蚊磅孽慚戳稟鄂饋垣濺咚鈣礁彰豁瞇磷雯墟迂瞻顱琉悼蝴揀渺眷憫汰懾嬸斐噓鑲炕宦趴繃窘襄珀囂拚酌濁毓撼嗜扛峭磕翹槽淌柵頹熏瑛頤忖'.decode("utf-8")]

def get_freqHanzi3500():
  return ['牡缀徊梨肪涕惫摹踱肘熔挚氯凛绎庶脯迭睦窍粥庵沧怠沁奕咙氨矗盔拇沛榻揣崭鞘鞠垦洽唾橱仕蜘痰袜峙柬蝉蟹谏鹃擎皓朕疤禺铲酶钝氓匣弧峨锥揪杠吭崛诬冉抒庚悍靡晦醋壕锯夭咦侈婢猾徘硝煽皂舵嗦狈靴捂疮郝苛秽茜搓芸酱赁檐饷蕉铀苔赦缎舷筷朔婪紊厮婿寥兢糙卦槐扒裴祀埔絮芭屉痪霄绽宵邑霖岔饵茄韧琪邹瑚憋殆噜忒忿衅淳悖髦孜粤隘濒铮畸剔坞篱淀蓦唬锣汀趾缉嫦斟鞍扳拴诅谟呃懦逞犁忏拧亥佟叱舜绊龚腮邸椒蔚湛狩眶栈薇肮瀑渣褂叽臀妞巍唔疚鲤戎肇笃辙娴阮札懊焘恤疹潇铝涤恃喽砌遁楞阱咎洼炳噬枫拷哆矶苇翩窒侬靶胰芜辫嚎妾幌踉佃葫皖拽滤睬俞匕谤嗤捍孵倪瘾敝匡磋绫淆尧蕊烘璋亢轧赂蝗榆骏诛勺梵炽笠颌闸狒樊镕垢瘟缪菇琦剃迸溺炫惚嗨陨赃羁臻嘀膳赣踌殉桔瞿闽豚掺沌惰喳椭咪霎侃猝窖戮祠瞩菁躇佬肋咄忡雍忱蕾跄硅伎炊钊蝠屎拭谛褪丞卉隧茸钳啃伢闺舔蹬挛眺袱陇殴柿梧惺弛侥琛捅酝薯曳澈锈稠眸咆簧鸥疡渎汲嬉脓骡穗槛拎巳邢廿搀曙樵隅筛谒倭痹猖佯肛奚甭抨蛾唠荧嵩漱酋攘诘篡睿噩怅盎徙鞅漓祟睫攸翎呛筐堑檀寅磊驭惘吠驮瑙炬痉曝恺胺萤敕筝幡霹竺烙毗鸠埠蒜阜嘈乒帷啄鳌毡阙褥搔笋冕狞韶骼蔼烹奄嫖沐噗岑蛟掳咏弩捻圃孚悴诣呱祁捶钠袄澎氮恪雏撮堰彷鹦晖犀腑沽橄掐亵龋嗒咀祺锚'.decode("utf-8"),
          '牡缀徊梨肪涕惫摹踱肘熔挚氯凛绎庶脯迭睦窍粥庵沧怠沁奕咙氨矗盔拇沛榻揣崭鞘鞠垦洽唾橱仕蜘痰袜峙柬蝉蟹谏鹃擎皓朕疤禺铲酶钝氓匣弧峨锥揪杠吭崛诬冉抒庚悍靡晦醋壕锯夭咦侈婢猾徘硝煽皂舵嗦狈靴捂疮郝苛秽茜搓芸酱赁檐饷蕉铀苔赦缎舷筷朔婪紊厮婿寥兢糙卦槐扒裴祀埔絮芭屉痪霄绽宵邑霖岔饵茄韧琪邹瑚憋殆噜忒忿衅淳悖髦孜粤隘濒铮畸剔坞篱淀蓦唬锣汀趾缉嫦斟鞍扳拴诅谟呃懦逞犁忏拧亥佟叱舜绊龚腮邸椒蔚湛狩眶栈薇肮瀑渣褂叽臀妞巍唔疚鲤戎肇笃辙娴阮札懊焘恤疹潇铝涤恃喽砌遁楞阱咎洼炳噬枫拷哆矶苇翩窒侬靶胰芜辫嚎妾幌踉佃葫皖拽滤睬俞匕谤嗤捍孵倪瘾敝匡磋绫淆尧蕊烘璋亢轧赂蝗榆骏诛勺梵炽笠颌闸狒樊镕垢瘟缪菇琦剃迸溺炫惚嗨陨赃羁臻嘀膳赣踌殉桔瞿闽豚掺沌惰喳椭咪霎侃猝窖戮祠瞩菁躇佬肋咄忡雍忱蕾跄硅伎炊钊蝠屎拭谛褪丞卉隧茸钳啃伢闺舔蹬挛眺袱陇殴柿梧惺弛侥琛捅酝薯曳澈锈稠眸咆簧鸥疡渎汲嬉脓骡穗槛拎巳邢廿搀曙樵隅筛谒倭痹猖佯肛奚甭抨蛾唠荧嵩漱酋攘诘篡睿噩怅盎徙鞅漓祟睫攸翎呛筐堑檀寅磊驭惘吠驮瑙炬痉曝恺胺萤敕筝幡霹竺烙毗鸠埠蒜阜嘈乒帷啄鳌毡阙褥搔笋冕狞韶骼蔼烹奄嫖沐噗岑蛟掳咏弩捻圃孚悴诣呱祁捶钠袄澎氮恪雏撮堰彷鹦晖犀腑沽橄掐亵龋嗒咀祺锚'.decode("utf-8")]

def get_hskB():
  return '一七万三上下不且世业东丢两个中丰为主举久么义之乐九也习书买乱了事二云互五些交产亮亲人亿什今介从他代以们件任休会伟但位低住体何作你使例侯便信俩倍倒候借假做停健傅像儿元先克全八公六共关兴其典内再冒写农冬决况冷净准凉几出刀分切划刚初利别刮到刻前剩力办加务动助努劳包化北医十千午半单卖南占卡危厂历原去参又友双反发取变口句只叫可史右号吃各合同名后向吗吧听吹呀告呐员呢周和咖咱咳哈响哥哪哭唱商啊啡啤啦喂喊喜喝嗯嗽嘛嘴器四回因团园困围国图圆在地场坏坐块坚城基堂墙增声处备复夏外多夜够大天太夫头女奶她好如妈妹始姐姑姓娘子字学孩它安完定宜实客室宴家容宿寄富寒对导封将小少尤就尺局层屋展山岁工左差己已市布师希带帮常帽干平年幸广床应店府度座庭康建开弟张当录彩影往很得心必志忘忙快念忽态怎怕思急总息您情惯想愉意感愿慢懂成我或戴户房所手才打扬批找技把报抬抱抽拉拍拾拿持挂指挤挺换掉掌排接推提握搞搬摆播操擦支收改放政故教敢散数整文斤新方旁旅族日旧早时明易星春昨是晚晨晴暖更最月有朋服望朝期本术机杂李村束条来杯板极果查树校样根桌桔桥检棵椅楚楼概橘次欢歌正步死段母每比毛民气水永求汉江汤汽没河治法注泳洗活派流浅济海消深清渴游湖满漂演澡火灯点炼烦烧热然照熟爬爱父爸片牛物特猪玩现班球理瓶生用电男画界留疼病痛白百的目直相省看真眼着睛睡知短矮研破础确碗碰磁示礼社祖祝神票福离秋种科租究空穿突窗立站章笑笔第等答简算篇篮米精糖系紧累红级纪纸练组细织绍经结给继绩续绿羊翻老考者而联肉育胜能脏脚脱脸腿自舍舒舞般船色艺节花苦英苹茶草药菜蓝蕉虽蛋行街衣表袜被装西要见观视览觉角解言计认讨让记讲许论设访评识诉词译试话该语误说请读课谁调谅谈谊谢象负责贵赛赢走起足跑跟路跳践踢身躺车轻较辅辆输辛边过迎运近还这进远连迟退送适通遇遍道那邮部都酒酸里重钟钢钱铅银错锻长门问间闻阳阴附院除险难集雨雪零需青静非面鞋音页须顾顿预领题颜风飞食饭饱饺饿馆首香马驾验骑高鱼鸡麻黄齐'.decode("utf-8")

def get_hskE():
  return '丈与专丝严临丽乎乏乒乓乘乡争于井亩享京仅仍仔付令仪仰价份仿企伍众优伙伞传伤伯估伸似余佛供依侵促俗保修俱倡值偏偷傍催傲傻允兄充光免兔党入兵具养册军冠冰冲冻减凡击列则创判制刷刺剧剪副割劝功励劲势勇勺匹区升卜卫印即却卷厅厉压厌厕厘厚厨县叉及叔受叠古另召台叶司吊吐吓否吨吩含启吵吸呆味呼命咐咬咽品哇哎哲哼善喷嗓嘿嚷固圈土圾址均坡垃型埋堆堵塑塔填境墨壁士壶央失夹夺奇奋奖套妇妙妻委姨姻婚嫂孔存季守宝宣害宽宾密察寸寻射尊尖尝尽尾居届属岛岸崇巧巨巩巴巾币帝席幅并庄庆序底庙延异弃弄式引弯弱弹强形彻征待律微德忆忍怒怜性怪恋恐恢恨恳悄悉悔悟悠悲惊惹愁愤慌慕慰懒戏战戚扁扇扎扑扔托扛扣执扩扫扭扮扰扶承抄抓投抖抗折抢护披担拆拐拒拔拖招拜拣拥拦择括拼按挑挖挡挥挨捆捉捕捞损捡捧据掀授掏探控措描插援搁搭摇摔摘撒撕撞攻效敌救敬敲斗料斜断施旗无既昏映显晒晓普景暂暑暗曾替朗木未朴朵杀杆材松构析林枪架某染柴柿标株格案桶梁梦梨梯械棉森植榜模欠欺款歇歉止此武歪殊毕毫毯汗池污沉沙油沿泛泥泪泼洋洒洞测浓浪浮涂涨液淡混添渐渠渡温港湿源滑滚滴漏漠激灭灰灵灾炮烂烈烟烤烫煤煮熊燃燥爷版牌牙牲牵牺犯状狗独狮狼猜猫献猴率玉王环玻珠璃瓜甜甩田由略疑疲瘦登皂皇皮盆益盐盒盖盗盘盼盾睁瞧矛石矿码砍硬碎碑磨禁秀私秒秘秩积称移程稍稳稻稼穷窄竞竟童端竹符筑策筷签管箭箱类粉粒粗粘粮糊糕糟素紫繁纠纤约纷纺线终绕绝统绢绪绳维综编缩缺罐网置美羡群羽翅耐耳聊职聪肃肚肝肠肤肥肩肯肺胃胆背胖胡胳胸脆脉脑脖脾腐腰膀膊臭至致舌航良艰苯范荣获菌萝营落著蔬薄藏虎虑虚虫蛇蜂蜜血补衫衬袋袖裙裤规触警订训议讯证诗诚详谓豆貌贡败货质购贯贴贸费贺资赔赞赶趁超越趟趣跃跌距跨跪踩蹲躲转轮软辉辟达迅迈违迫述迷迹追逃选透逐递途逗逛速造逢逼遭遵避邀邻郊郎配酱醉醋醒采释野量金针钓钻铁铃铜铺锅锐键镜闪闭闯闲闹阅阔队防阵阶阿际陆降限陪随隔雄雷雾露靠革顶项顺颗飘餐饼馒骂骄骗骨鬼鲜鸟鹅麦默鼓鼻龄龙'.decode("utf-8")

def get_hskI():
  return '丁丑丘丙丛丧串丸乖乙予亏亚亡亭仇仓仗伊伴伺佩佳侧侨侮俄俏俯倘倚倦债倾偶偿僚僵兑兰兼兽冤冶凑凝凭凳凶凿刊删削剖剥劣勃勉勤勾匀匆匙华协博卧卵卸厢叙叭叹吞吻吼呵咙咸哀哆哗哟哦哨唇唤售喇喉喘喽嗦嘱噢囱圣坑坝坟坦垂垄垫垮域培堤塌塞墓墟壤壮壳夸奈奔奠奥奴妥妨姥姿威娃娱娶婆婴婶媳嫁嫌嫩孙孤宁宅宇宏宗官宙审宪宫宵寂寓寞寡寿尔尘尚屁屈屿岗岩峡峰崖崭巷帐帘帜幕幢幻幼库废廊廓弓归彼径徒御循忠怀怖怨恰恶患悦悬惕惜惦惨惭愈愚愧慎慧憾截扒扯抑抛抵抹押拢拧拨拳拴挣挫振挽捏捷掠掩揉揪揭搂搅搓搜摄摊摧摩撑撤攀敏斥斯旋旦旬旱昆晃晕晰智暴曲末朽权枉枕枝枯柄柏柔柜柱柳核栽桃档桩梅梳棋棍棒棚椒楞横欣歼残殖殿毁毅毒氏氓氛氧汇沟沸沾泌泡波泽洁洪浆浇浑浴浸涉涌润淆淋淹渔渣溅溉溜溶滥滩漆漫潮灌灸灿炉炒炸烁烛焊焦焰煌煎熬燕爆爹牢牧犹狂狠狡狱猎猛猾猿珍琴瓣瓦瓷甘甚甭甲申畅畔番疆疗疯疾症痕癌皱盏监盛盟盯盲眉眠眯督瞎瞒瞪矩砖砸碍碱秧稀税稚稿窑窜窟窿竭笼筋筐筒籍粥粪粱索纯纱纲纵纹绑络缓缘缚缝缸罚罢罩罪署翁翘耀耍耕耗耽聚肌股肿胀胁胞胶腔腾膏膨舅舰舱艘艳芽苍苗若茅荐荒菠萄葡蒙蒸蓬蔑虾蚀蚊蚕蛙蜡蝇蝴蝶蠢衡衰衷袍袭袱裁裂裕裹譬讶讽诊诞询诬诵谋谜谣谦谨谷豪豫财贫贱赏赚赠赤趴踊踏蹄蹈蹬躁轨载辈辑辜辞辣辩辱返逝逮逻遗遥遮酬酷鉴钉钞钥钩铝铲铸锁锈锡锣镇镑闷阂阻陈陌陡陵陷隐障隶雇雕震霉霜顷顽颂额颤饥饮饰饲饶驮驴驶驻驼骆骚骤魂鲸鸣鸭鸽黎齿'.decode("utf-8")

def get_hskA():
  return '丹乃乌乔乞乳亢亦仁仆仙伏伐伪伶佣侄侈侍侣侦俊俐俘俭储僻兆兜兢冈凄凌凤凯凰凸凹函刁刃刑刨券刹剂剃剑劈劫勒勘勿匠匪卑卓厦叁叛叨叮叼吁吉君吟呈呕呜呻咋咏咨哄哑唆唐唠唯唾啃啄啥啸喻嗅嘉嘲噪嚼囊坊坛坯垒垦埠堕堡堪塘壹夕奉奏奢奸妄妆妒妖姆姜娇媒嫉孕孝宰寇寨寺尸尼尿屉屎屏屑屠屡履屯岂岔岭峻崩嵌川州巡巫帅帆帖幽庞庸廉弊弥弦彰役徊徐徘徽忌忧怠怯恒恩恭恼悼惋惑惠惧惩惫惰慈慨慷憋戒抚抠抡拄拇拌拓拘拙拟拱拽挎挚挟挠挪捅捌捍捎捐捣捶捻掂掐掘掰掷掺揍揽搀搏携摸撇撵擅攒敞敷斑斧斩旨旷旺昂昌昧昼晋晌晤晶晾暄暮曰杏杜杠杨杰枚枣柒柠柬栋栏栗桂桅框桐桑桨梗梢梧棕棱棺椭榆榨榴榷槐槽樱橡檬欲歧歹殃殴毙氢氮汁汛汞汪汰汹沃沏沛沥沫沼泄泉泊泣泰泻津洲洽浊浩涕涛涝涤淀淇淘淫渗渺湾溃溪滋滔滞滤滨潜潦潭澄瀑灶炊炎炕炭烘烹熄熏熔爪爽犁犬狈狐狭狸猖玖玫玲珊珑琢瑚瑞瑰畏畜畴疏疙疤疫疮痒痪痰痴痹瘟瘤瘩瘫瘸皆盈眨眶睦睬睹瞥瞩瞻砂砌硅硫碌碟碧碳磋磕磷祥祸禽禾秃秆秉秤秽稠穆穗穴窃窝竖竿笆笋笛笨筛筝筹箩篱簸籽粹糠絮纳绅绒绘绞绣绵绷绸缀缎缔缠缴罕罗羞羿翔翠翼耸耻聋聘肆肖肢肪肾脂脊腊腥腮腹膛膜膝臂臣舆舟舵舶艇艾芒芝芦芬芭芳芹苏茂茄茎茧茫荔荡荷莫莲菇菊萌萍董葫葬葱葵蒂蒜蓄蔓蔗蔼蔽蕴蕾薪薯藤蘑虏虹蚁蚂蛛蛮蛾蜓蜘蜻蝉蝗融螺衅衍衔袄裳覆誉誓讥讹讼诈诧诫诱诸诽谎谐谗谤谬谱谴豁豌贝贞贤贩贪贬贰贷贼贿赂赋赌赖赴趋跺踌踪蹋蹦蹭躇躬轧轰轿辐辖辙辨辫辰辽迁逆逊遣邦邪郁郑鄙酌酗酝酶酿钙钦钮钳铀铭链销锋锌锤锦锯锹镁镰镶闸闺阀阁阐陋陶隆隘隙隧雀雁雅雌雹霍霞霸靴鞠鞭韧韵颁颇颈颊频颖颠饪馈馋驰驱驳骡髦魄魔鲁鸦鹊鹰鹿鼠龟黑'.decode("utf-8")


def get_tw1():
  return '一人下上大子小不中天心水出生地如年有自事來長為面家氣起高動國得開道學以可用多好和所後是時著過說了去在沒到要能做常就樣個又他的這也很外同成作發會知對點看等想我候都最花那還麼你三分方日打老物書然二而定果前間當十叫因從現像種裡們意回些力公手西車明情頭見走東經話樂比把體兩快正才太吃真給第覺只每山白兒聲本美帶進位使之行法次弟寫跟色電字於表愛問錢邊聽再完幾但名身風月全放路別己相什早文合重理喜或工四被媽爸部'.decode("utf-8")

def get_tw2():
  return '直空變師友歡各無音球數興已拿讀口平加活原畫實應海先住教處難今課五校她眼女望親少跑光衣服接清場新父向期許玩朋呢由星視讓主通運六形妹哥坐條安門馬機受飛病笑感節樹告記請件它買隻午怎內民其王考飯母習孩死神信紅魚亮立嗎世百房張結功非便晚並金木代業語元容將此連睡怕火河雨食關總更且指量目報滿故遠班類題答化度往八反交利紙強解管精九具害跳麗幫找號流片收夜界苦陽照遊希'.decode("utf-8")

def get_tw3():
  return '半步保倒熱包整姊古林算與輕器較計牠入性軍菜園燈歌注土南忙該北失皮草黃近假唱排船試臺始共命隊黑送乾養久認思圖論觀卻雖社賽石特華傳任念士毛筆萬禮七級造青客香影助改穿息停傷演講醫越慢句建提言義葉戰鳥必喝趕吧升市品育屋求室轉除訴足院雲腳男奇英掉備景象綠緊辦錯識壞庭政稱婆細落圓者取裝決肉休刻易根離藥練角積千夫布春亂田周約終例響員線產示牛守何呼參溫選戲護忽剛準趣敢漸夠及式狗極奶設啊首料段酒深底尺省居板單消留隨哪令血油城費存怪急洗破勞痛農舞談舉謝塊敬鐘旁換歲賣靜臉詞官至阿餐街爺調切呀則哭科商集背座統達蟲忘持願驗誰拉味救童鄉順福環雙站討灣努睛'.decode("utf-8")

def get_tw4():
  return '冷夏游漂朝右區爭斷鐵止左治務專推復短領究竹規需秋負吸您盡伯架搖導依健康境操燒爬沙差野腦雞永桌遇引狀製叔曾詩吵展簡府史格程圍床術似組項里德未米善群鼓團責增兵殺票察樓寶乘淨潔續係曲洋堂牙良店待茶彩勝鬧顧免吹困汽旅靠查江甲姓制眾惡般低紀替另耳司局防枝射散辛顏朵拍兄投齊懷充龍冰灰羊洞浪針敗富雄險幸缺速棒鮮價初列適抓置乎端瓜夢廣掃植質玉絲盤豆基頂固研族刀李貨貴嘴橋藏姑杯染煩晨某警貓弄志泥修彈糖臨驚冬危孝勇突追零賞擔昨巴迷陳聞衛抱堆涼陸優避幼捉慣肯支罵琴確密祖絕章標伸互台啦骨克須附營藍材蛋武拜珠暗輪壓序季革值烈閃掛減嚴煙退麻寒蓋壯娘益勤誠鞋偉惜搬績顯即裏戶滑忍陣窗勢莊孔素供印微資擊態楚鬼婦盛漢姐末胡若配議岸熟織泳屬舊財軟閒躲登髮派銀帝偷預層辭陰尊敵村瓶騎嚇孫虎封付袋途箱激繼彎肚懂兔雪翻池紛採鄰麵否奮醒剩'.decode("utf-8")

def get_tw5():
  return '冒甚仍煮測尚縣堅寬劇聯檢獨據犯俗粉招案圈異補廠迎哈述幹牆按烏技攻胞歷肥模巧刺拔湯鼠榮鼻暴館卡抗束訓累超載旗恐祝碰餓含乙壁珍智舒暖隔獎衝擦鬆廳露液施際濟丟維況份竟佛鏡律尤蝶湖典源歸靈限波毒鬥弱揮鉛誤鋼蘇概讚粗介抽柔借摸豬輸繩欣猜碗稻忠斤伴妙噴戴陪踏聰沈職雜娃尾郵盒脾寄透圾酸蟻凡型皇效腿棵剪折厚套權慶亡尖君松怒脫飲塞貝奔泡挑逃淡創悲掌厭憂撞默擺佩畢既髒愉顆倍致島窮恨捕喊郊羅玻偏棉鈴頓廢璃槍吐汗帽筒豐勸飄享抬捨椅籃輛餘錄洲罪藝移硬率疑遺繁構燃螞私均齒範偶爾揚森轎桃蘭探符威殘羽損釣距降雅禍災淚猛滅飽滴貌箭舅篇獻蜜仁仙溜聖刷姿棄甜貼播潮遲粒奏沖欺廚擠紹勵頁蝴宗證曆婚釋哇築幻斯徒填縮橫丈污徑普獲遍糕昏亞愈輝碎爽莫訪殼廟輩侵宮腰繞敲暑慰卷耕梯餅鎮晴垃丁孤甘秀宜倫惠週溝擇鴨貢跌搶懶疼恩耐憐潑乖編振秦薄階塗略禁墨妻觸儀插溪沿混聚抵阻縫番汁邦胖核港批股疾副幕銅鍋坡遭牽宣炸握劉濕扇鹿博晶搭獵姨幅膀牌雷吳夾奉拖訂臭隆寧漆蓮賴慕辨匆描摘憶賺州朗燭咬捐筋慧'.decode("utf-8")

def get_tw6():
  return '仔鹽斑礦患秒裳磨虛隱京延柱胸逐央穀僅哦浮垂納斜緣穩承麥迫桶逛澡蕉吉蓄評獸眠怨慮罩仰臣盆閉糊爛仗促疲詳儲鵝恢膽谷苗蜂窩埋笨割漫賢簿傲嘗咪巨扶炎滾駕籠扮勉拾悟渴騙驕牲踢譬佳慈祥飾颱祭慨謀彼碼執複憑歪梅稍蒸孟菌喪屈旋淺秩索尋監獅噹瓦席井判唐臂宋挖融闊協匪占貧寸川庫震叢灌猴肩愁蒼糧蠟弓純衡蛙頑儘網呆冠悶棋醉寂淘慌躺腸狂芳啟蛇楊津敏淋傘誇瘦擁穫遵夕吞漁撲諒謂氧溶括妳干劃喻委跡烤喔策舍韓毫撿尼黨歐佈罷膚紫塵覆緒豪籍壘荒膠芽袖幣魯眉奪厲疊劑岩映郎航捲稀慘腐撥濃譽串巷翅罰汪澆培嫁障枯釘嘉魔鑽聊熊蝦閱曉臟伍悄狼采胃喉淹雀矮爆罐悔拳拼燙灘款駐蔣暫徵裂猶叩蒙紋耀版稅額系貫遷縱域殖藉踐授攝恥牧炮燕塑擴仿億伏舌斗旦戒赤柳泉紗壽鳴摩緩騰巾兇侯哲傑賀哀胎爐竿擋競泄肌幽挺荷療艱齡恰羞貪陶梨鍵宇寺扯牢抖倦渡遙鄭駛轟趁羨摔筷嘻翁霧茫惱磁謙挾側陷氏殊呈諸冊欲腔舟砲梁裁惰宿疏劍雕螺辯乏拒循憤擾繪蘿鷹叮炒虹扣愚稿佔抹柴嫩趙鴉虧贈睜賓褲扁控笛滋購嫂寞坦症敘桿匹悅瘋欄躍划窄脆嬰仇柏暢糾鞭狠喚糟蚊蟹踩焦綿伙侍咕畏挨堪碌翠鍊灑稚犧黴丹嬌娛綁諾亦韻衰刑售傾盲乃辱毀繫迅俄帳託盜欠崇紮肅鳳卵桂違尿役皆痕譜耶脖螂乞昆朱塔漏遮慎黏謹邀勁廉魂准悠戚歇僕徹誕櫃簽覽砍瞧咐瑰托巡洪撒伐后宏姆恆耍倉屑壺湧惹迪倆鈔肝泰奧爪添愧塘譯坑峰抄販矩捧喘闖劣'.decode("utf-8")

def get_tw7():
  return '傍龜搜腹泛蠶螢犬拘溼械懸脈凝珊恭漠蕩啞唯綜曬乳祇租拋宴遞漲銷兼申媒惑棍葬墳礙贊襲芬援逼肺嫌懼奴袍狹遣蔬曹盼摺餵刊扭杜漿薪鎖召臥悉絡誌撫樸橘杆玲寓唉榨皂燥娥嘩謎砂鋒磚勾呵昌昂昇妨郭翔歉芒徐浴廊盪矛盾蹟囊譏莖鋪晉祕鋸畜督蹴旨醜纏碳晒肢艇銳蔔披晃墓哩彿頸棟湊輔籌浸蕭茂捷賭枚屍潛蹤莉逗董翹襯澈闢蜓征逢瑞碧閣錦翼于扎吾刮析返缸掙葡誓霞醬攤攪廁玫琳奸押嘆蓬吟拆枕泊盈凍迴堡敦脹腫鉤馳槽賠嶺咳匙晝廈慚懇瞪謊嘛吩傻裕壤陌儉敷賜氛哎帆跪蹈企訟軸丙妖盟賊脊惟獄綱轔予措蔡削潤澤酬衫殿邪炭債裙鍾彷宅亭棚娶凹潭邱丸劫宰夥艦蘆估旺榕勒栽脅盞贏旱揭渾扔卑丘奈秘酷謠鴿盯匠勃墊蠅廷併哄屏淒凱註誼錶魏癢蠻叭岡挫撐墾憲澳熄顛枉暈浩喇診宙嚕囉溉歎俊昭榜佑嬸審脂煤紡瓷蝕硫弦冤膜柄禽誘崗掩喬坊妥涉秤陵鑿胳豈徽蟀蟋鱗帥仲忌銘橡臘凸僑挽裹蜻咱紐偽儒簧玄桑兆瓣飼鏟絨萊杖泣誦允吱洩埃梳滔槓鬍礎嫦螃株霜岳叛洛巢媚償糞豔歹眨萄蘋侮俱彰跨聳訊拱俯躬飢菊催黎濫秧撕鍛箏吼緯孓凶賤嘟屆擲姻穴纖契瞭鯉蟑鏈截署駝蟬嗡敝貿禾姜寡陋綴斥吏邋戀叉耗絮薩攏嚼驅屁峪伊腺辰柯棲勿鹹揉疆猩剝宵怡軌捏喧煉鄙瞎蹦芭祈筍蛛皺頰穗饒櫻喲蜘闆焰澄繳攔址毅燦攜匈哼濱凌淑茄陡薯禱茅逝啼遼邁寵霸耽嘲耘嚨涕泌雉廿趨擱殷顫艾鬚娜絃雌冕帘繡僧兮甫睦迸膝軀醋偵奢掀頌熬緻鋤吻妝框掘撤綢銜豎錫襟孕襪蕃頻丑岔搗僻鯨躁聾咚浙狐怯咽栗竭赫堵蔗繃唸傢俠衍慾碩澎嚮嚷煞拌嘿訝嗨倡狸碟搞暮吊朽芝烘焚彌伶呂煌懈逍喂毽颳巫婉溺帕洶欽嬉藹暉'.decode("utf-8")

def get_tw8():
  return '錐撮纔賦鑲醱庸抑氫恕皿褐醮盧鏃竊樞澱鹼頗勻逸斧詢蒲緞璧姪尉堤凳禦粽寢妒膏濁啄禿媳瑚舜卜戈腕煎碑劈潰曠余蚓淇蚯橙趟卿豹菲艙濛藤拓峽噪爍嶼崩札冶喳毯隋餒駱鞠骯崖梭叨哨瑪扛咖啡傅萍楓膩櫥馨俘徊倘瀑鵑鏢鉋鼎汙蔽蔓邑彫雇曰沉募鬱詐妄沸荊匯隙稽沾洽粹簷驟鏽逆弔杏券倚脣辣悼棺鰭稷艘諧龐寇壇攀貯肪鶴冥弊蹄驢罕陝蹲曼斬蔭呱茉唷娟葛夷佐剖唇茲屠棗粥溢輯扒沃拇俐哉凋晏爹袁梢敞棧萎屢翩戳簾禹崑頃琵琶嗽骼塌癌矢嗜埔唧嗓牡峻奠搓濤怖卒拂赴樑鴻剎軒凰涯琅棕嗚嘔綽潦擅瀝鷗柿趴辜葦餃槳憾掏鑰羿撈鋁卓苔頒蔚甩濺幡喫酉鏜郾烹釆瀋癡赳搧爵髓匣顎鏤祀桓畝刃婿擬韌馴瑣藺昧縷藻卦范哺閥攙釀菱瓏衷御淵貸遜騷鑼淪廂菩鈕遂瞞籤阮塾囑乒弧兜鑑毋疹耿摧滲窯豫蘊摟穌喃疫幢拐貞惶渣酥猿瑟丫沫侶訣搏肆蜀撇誨僵寮咻笠楣餌徘犄齣汝汰蛀渺菁嫉腮懦竅丐倩圃捆砰廖蚣蜈曳琉詹瞬癮鷺賈咯韋榴霉穎崙懊嚥拯虫鏝鏘阜彭曝蕊矣卅苛淫履苟庶莽孽酌焉趾椎稜箕蓆廝撓黛戊菸餞軻胚轄肴嬴灶函歧勘椒雁聘篤霍禪籬云腎締縛矯篷簫礫瑜孵朦朧拙掠舵粟祿裸攘饑兀伺肘咒妮砌虐揀棘膨諷鮑曜辮黯几晰隄嗅卸垢蛾墜瘤蔥穆靡麟旬臼侈帛昔屎苞桐彬梧涵淮鈍慷嘰撰頹檀檯穢薰矇繭蠢恍眶莢釦痺誡樁噸糙駿颼瞇嗯絞羹跋痰蕪乓蚱佰柵疤紳渦皓馮噓蕾瞻邏欖杭莓嚐柚鏖疸鏑糸坎霄奄咸啃逞睹嘮檔礁屜皎窒琪蒐瑩鯊汴沂愣帖瘡唆膊懲鵲筏稠箇酵餡訢駁鑄尸妓狡梗筐黍窠摹薦壩硼霆甌簍邵埂擷郡濾炊雯瑾衙筵簇磅囚眷暇滯魄翰齋屯秉剔荼訛婷犀碘葵虞廓槌滌熔蒜磊勳髻氈隸竄藩甸肛拴祠紊悽烽斟煦嘈幟憫緬檻鐺冉炕蛹隧姦腥夭卯沼梓鈞窪閩駭糠闌亥絹彆蹺荀飪弛覓倔畔虔兢嘍嚏羲揍蒂鶯仕弘沛宛庚郁涎豚堯湘漓綸肇凜墮撩夸吶呻坷惺揪蛻跤噎薇鵬繽跺踴晾睏墅蜿嚀絏艷潘亨抒狄俏彥嗦垮悵痘蝸霓瞰瞌瀰蜢咦槃砝兗鏍隹鹵詭帚芥硝猾斂愆醃橢魑粱忿匿貶稟窟賄閨賬贅咎俸捻氯鈣嗣葫磕醇熾頤輿瀾驛妾蚌梵璋蝨褒鴦鴛窿鼬襖鰻癲鈸螳缶唾鳩魁瀉轍肋吝庇忱扼沐汲剃怠峭恣殉婢袒揣硯萌楷詰嗶綻誣碾褥膿褶錘檬檸臍簸贖鬢韭烙嵌徨菠跛閏熨稼樺諜輾殯餾麓姥紂滓軾龔蘸騫灼窺甥渠閑匡夙佣刨肖陀宦茹帷犁喀詠鉅漾綵蓉嘶樟橄擎斃糜襄闔鑒丰仄侃咀氓姚倭狽笆愷粵虜幔漣瞄噗癟蠕鰓顱氾斛詣漩骰鞏蹋亢乍妃刪吠扳芋拭浦惕眺絆缽羚莎彙椰煥遐靖熙廬佃坪杰穹倖悚祟蚪唬崎淳淅啾揩揖蛟貳榔痲綑僥樊膛蝌撼篙嬤瀟隴鸚芯閔滕燼鞦饅鰍巔吋渤祺矗'.decode("utf-8")

def get_tw9():
  return '拚芹茁餚蹇挪鈉砸誅豁謬粧勺圭兌豕軋悍氨晦厥蛤搔裘辟榻諱踵濯澀瞳釐牘攬沌紉紇捎涓逕戟琢漬瘩蝗篡錠篾謗伕迄舀痠嗇耒鞅憔俺蟯犰靴孜姬茸遏靶寥髦摯膳錨坍怔冑惋舶莒傀詔滷銲簌騾讒躡驪抿咨楞瓊刁戎杉汞拗炙芙芸剋恬殃倣朔眩胰偃匾釵孳寐氮腋傭榆溯滄瑕睫逾鉗雍嘎漱瑤綺餉嘯墟瘠緝諫閻孺嶽薛雛藕礬囂巖纜鸞尹朴伽妞杓沮峙柩苑哽挈桅砥耙茵蚤寅徙惘敕聆脯壹掣逮馭瑯瘁睬裔摻榛撬澗緘鄧褪踱壕磯縹蟆遽黝瀆蹙繹譁麒曦巍巒霽攣籮匕爻卉丞忪枴倪浹畚淞痙袱剷徬臧嘹噯薔贍韆酗捶筧憧踫櫓躪叼珮罣坤壑俞痴箸踞擂屹吭竺炯啪悸湃僱潺擄瘴瀚嗆楠舔壢蘚蝠翱悛翾鎔尪寨矽剌芻娼隅鉀隕嫡憎毆篆鋅鍍贓汎佻徇珪毬諂燐殮臀鴃縴餽瓤籲姒佗糨僚鵠并蜷靛饞巳藷殳鎗叱吁牟迂侖庖弩沽咧咿恃恤栓涔淤淆疵盔赦喙惻窘萃証貽酣嗟慄遁酪隘嶄槐箋褂銖鳶蔑鞍駟擒燎瓢縐謁諭鞘骸鬨濡臆膺蹊癖譎竇癬癱羈匝弗疋戌舛岐杞姍沱泗疙疚盂奕恫柬殆盹籽苒迭閂厝奚胯荏偕埠掖旌晤淙眸舷嵐窖絢塢牒瑙綏馱僮幛瘧箔綾輓瘢磋諄踝閭噩澹瘸篩螟鴣儡櫛禧繆薑褻闈騁繕藐鎚鬃壟瀕疇蹶鶉嚶礪纂癩鐲孿蠹釁鑾丕朮艮阡囪咩舢奘胱陛惦惚掄捺粕蛆湄稈筑楨筠葆詫賂鄒睿撢豌樽諺錳醣瀏鯽籐譴髏饕鰾齲劾徠悴惆捱揹蛔肄雹慫骷噢懋瀘鷥螄廾圳瓠逖痣鉑湉墩柑桀啤湛聒剿愴駒霖鏗儷仆叵亙旭佇孚冽拄狙祁柢炬癸迥娓恙栩盎砧訖偎倏扈涸畦痊硃笙愕扉棠剽嶇榭漪犒賑嫻頡憩憊樵燄縈蕈諦檜谿檳癒繚譚糰醺霹懿轡靄吒戍抉阱杷枇姣蚩淬渙琦甦腱滬蓓緲緹諉熹濘璨螫鵡鐮儼靨壬仟拎唏烊啕漳閡蝙遨瞼齬顥蒿轂榫箝謄舂皴椴踉矜孑戾罔拽拷耆猥腑飭葷釉閘嘖輻錚駢磷簪邇闕蟾麝忖攸狎俎玷眇胥迦迢俾娩悌涅窈舐茴衽莘蛉袞斐焙痢媾搪睢稔裊賃熒睽蜥誚賒諛赭銬儕壅轅鎂黜襠癥蘑闡鐸鷂韃吆囤灸牴娉涮窕啻鈐閎飧猷睪蓊遢銨憚暱橈褡諮頷曖覲糯蠣襬蠱鱔鬣妯陂娌啁跆蜊瘓蓀諼檮蠍蠡黷綃嘬噲尢禺鍔鐳噭么佯拈杳邸垣炳冢悖晌祚荐袂崔庵焊貂幌畸煽戮瞑髯寰罹霎擘甕蟠馥鱉纓仃厄汀牝妣妍岑岌佬剁咋杵杪泱俚咫垠奎宥毗炫狩盃盅竽胛胝苓苯叟哮屐峨疽祗紜羔舫荔茱茨訐訕釜啖堊孰戛淌笞翎訥赧喋媛愜摒棹渭湍渝湎翕腓腴菰訶軼塭愾暄滂蜃詼詮賅鈿嘀塹嫖嫣幗慟槁漕禎翡輒銑韶潸皚褓褊諍踟輟輦魅冀噤噬瞥蕨靦嚎嬪曙燴獰磺翳膾賸麋燻罈邃鎢鎳鎬懵羶羸躇麴懺懾殲躊籟韁驍攫靂顰矚汐尬汨汾芍咆怩泅泠侷氟苜觔訃迤酋倌唔娑氦氤涇珞祐啣圉婪彗悻掬涿猙痍翌莞荻釧傖喟堰渲琺詛跎跚隍戢搽楫煬稞葩氳憬璀蓿駙橇盥磬錙鴕尷檣濬燬褸謐醞攆擻獷薺謨蹣蹬饉騖鯧鵪襤躅夔斕櫺躋齜齦鷓齪邐饜刈羌臾洌洮洫敉偌恿荸幀萇媲毓溥碉榦艋褚嫵撙潼魷暹燉璜瞟縑臻蹂繅臃鍥鍬鍚鮪聶躂齟躑霾鑷窣阢浬偭搆煨蜆嫘閤縵艸岍紿鴟悃恚笄愊掰諢彀橛袤搠螅汛梟遑弋仞彤枸疣秣蛄陬嗉緇遛鴆璣獺韜鑠聿呎迆昊痔硎萋蛐碣膈麾儐彊縞擰鐫齧庠曷紲跼縊籀淀懃迕獃掐裱脛芎垛悁浞埸翊冗咄虱豺梆彪嗤嵩銓瘟駑蕙擢罄犢圩佞佚吮杠沁怏怵怛戕杼杲泯芟亟俟哂囿姘弭拮挂斫柞洱珀紆耄剜唁浚砭砟紕胭胼臬茗陞匐啜唳婁捫烯猖絀脩莠趺弼惴棣渥湮痞竣耋腆菅菽萸蛭詁詆鄂塚搾楔滇睨筮萱萼雋飴匱嗷嫗寤犖甄綬蓑蜴裨鉸鉻颯撳牖箴銻噥噱璞瞠輳霏髭黔檄檐癆鼾穠謫魎魍黠櫚璽藪孀鰥儻囈衢贛鱷鱸迓毳稗蜮攛乩伉仳刎妁汕囫妊沆汶甬肓阪侏侑卹呷坼岫帑忝抨歿沬肱肫匍奐泵牯胤倨俳圄捍朕桔涌痂皋皰砷迺婀婊崢捩旎莧蚵孱愎愀揆湔琥琨皖腌菴飩勦嗑塋媼慍楝溴睞睥蜇貉輊鈷奩愿慵摑斡旖暝榷獐瘍翟蒞靼劊嬋撚樅犛獗誹輜鋇噙曇篦縉褫覦諳遴錮餛鴒嚅嶸濠燧糢糝縲聱薜蟒鮫懣癘穡簣闐颺瀨鏨鯛醴囁矓驀禳躓鑣魘齷黌阨岬徂痀煒摽樗遯嚓卞卮佝呃忸枋玟疝祉苧娠宸峴晁訌軔陘淄淦袈堝嵇幃廄棻湲絰覃逶溧痳絛裟豢鉍嗾裴儂槨潯緙鄱鋰頫麩劓噶氅燜縝蕞踹錕覬蹉邂鍰闋鮭瞿繒邈鯖孃櫬蠔囌臢鱖灞灤釅丌苹恧逑皁枘夯砒莩橐籙鑊鬻籪囔汆芃坨咷耷嘧漚餑蕁瞵儵亹沅呸岷泓玨昱枰柒炤甭迨捌浥盍軏邕釭釩氬湣琯詖嗥僖暨遘噫撾濂璟甍簑鄴鄹壙璿鎘蹼瀲瓖饗酈籥鸛枓舖噁椿粘厘銹蜒伎哆枷恁覷匚忐蝟熏捋謔轆宕僂忤旳坳妺紈笈掂嗔摜閫罅枒觚頇蒔噘鐙顢扙扺剮梏揠椪嗩糗癈酤碴餧豸璇瀠眈胺棱痼摳潢篋圜螓繐泫咭秫莪喁甯菖隉鳧踅儆嶙醍蹚鵓鶻鰲鷙癰襻驤帔怦桉烜瓞罝圇桴欷莨喨喈堞棼渟腄葯酯撂瞅噌撟獢璉箬噠嬗歔擤檁薤螯鎯魈鎧鞫韙蹻騶齎柘涷酚羡搨摁楂楬鉬廒摶槎裰廡槿嚄謚鯪蠑醵颲菹廌蚜勛觴霤驥灴垕徼蹀薏闇駸礡鐐鬟呶弈徉疥虺狷疳荃敖晷楮菟戡溘煖葭貲鉚慇裯誑嶔磐耦銼儔冪嬝耨屨薊螻簞鞣鼕瀛巉罌鐃驃爨囡扦旮汊网芡凄哧粑猗逋硜嵬溷蜍觥跬跣遄嘵鴇閽謾鏦鯢鐿鶼弁刖劬孛坩岱芷恪皈胄苣酊倥倀崁捂桁罟郝崛崧徜梃梔蚶豉軛雩傚剴崴巽愒絳菔蛞賁鈑陲愍楹煆瑛碓裒詬訾酩髡僭膂蜩誥貍儈墀嬈畿瞋羯膘蝓懍撻翮霑壎濮蟈彝瞽薹鎊餿餮襞臚譫霰鼯囀瓔羼鰱鑤讖鑪鱟鼇讜乜尥抔旰杌芊怜旻邯俛敁苕苤恝捅旃栲狺罡惓晢眵酖堙嵫敪矬稂稊詈暌跫慪罳蒻裾潻糅衚鄲醅嶮燋縕蕕諤錛鮒鮐檎蕷貔蹐鎡鍼闃髽聵蟥蹡騑髀鵜繯譊譖鏹饈蠖糲衊鷇鷃扑氐氖妤抆邢兕劻昀昕秈芣俑柙柝洸洵玳畎畋疢娣胴舨衹逅郢匏埤庾渚琊紼耜脰莆逵鈇傯嵯弒暘瑁瘀痿粳萵鉉麂劂塽夤搴摭殤潟箠篌誶賡暸瘺磧檗燠磴繈賻颶櫂臏蹕櫝譙霪譟躉儸曩鼙鼴髑髖韉仂菇'.decode("utf-8")


def get_top1():
  return '一七三上下不世中久乖九也乾亂了事二五些交亮人什今介他以件休但位低住作你來便係信個們倒候借假做停健偷傘備像元先克兒全兩八公六共再冒冬冰冷出刀分別到刷前剛力功加努動務包北匙十千午半南卡危原厭去參又叉友口句只叫可右司吃同名向吧吵吹告呢周味和咖哥哪哭唱商啊問啡喂喜喝單嗎嘴四回因國園圓圖在地坐城堡報場塊壞士夏外多夠大天太奇套女奶她好如妹始姐姓姨婚媽子字孩學安完定宜客室害家容宿寄寒寓察寫封對小少就局屋山工左巧差己已巴市希師帶常帽幫年幾床店庭康廁廚廳弟張影往很後得從德心必忘忙快念怎怕思急怪恭息您情想意愛感慢慣慶懂應成我或戴戶户房所手才打托找把抱拉拍拿掃掉掛接推換搬摩擦收改放故教數文料斤新方旁旅日早明易星春昨是時晚景晴暑暖更書最會月有朋服望期木末本朵杯東林果枝校桌條棒森棵椅楚業樂樓樣樹橋機次歌歡正步歲每比毛氣水永汁池決汽沒沙河油法注泳洗活海消涼淨清渴游湯準滑漂漢澡火炸為烤無然照煩煮熱燈爬父爸爺牆片牙牛物特狗猜玩班現球瓜瓶甜生用男界留畫當疼病痛瘦發白百的皮盒盤目直相看真眼睛睡知短矮石破碗碼祝票禮秋科程種空穿窗站笑第筆等答筷算箱節簡籃米糕糖紀約紅紙級累紹結給統經綠網緊練總績羊美習老考耳聊聞聰聲聽肉肚胖能腦腳腿臉自興舊舍舒舞船色花苦英茶草菜著藍藥蘋號蛋行衣衫袋被裙裝裡褲襯西要見視親覺解言計討記許訴試話該認語說誰課談請講謝識警護讀讓豬貓貨貴買賣走起超越趣足跑跟路跳踏踢身車較輕輛辛辦迎近送這通進遊運遍過道遠遲還邊那部郵都鄉酒酸醫重鉛銀錢錯錶鏡鐘鑰長門開間關阿附院陰陽隨險隻雖雙雞離難雨雪雲零電需靜非面鞋韓音須頭題顏願風飛食飯飲飽餃餅餐餓館香馬騎髒體高髮鬧魚鳥麗麵麻麼黃黑點'.decode("utf-8")

def get_top2():
  return '丟主互付代任份何使例供值兄光內其具典切利刮刻剩劃助化區升卻受台各合呀咳品哎啤啦嗯嗽嘛器嚴困土址填境增夜妳姊季它富實將尤尺居布平底度廣建弄式形忽態扔抬抽拜指排提握搶摘播擇擔擠支救敢散整替未束板架查根梯極概橘檢歉死段殺母民求況洋流淡深淺湖滿演熟燒玉理環產由畢研確神秒租究立章童笨管精細繼續罵肯育背脫臭與舉萄萬葡處街表裏複襪觀訪設詞誠誤調諒論議變豐負責費貼資賽趕躺輸轉連週遇選郊鄰醋醬釋里金錄除陪陸青響頁預頓領顧颱首鹽鼻齊齒'.decode("utf-8")

def get_top3():
  return '丁丈且丙並之乎乏乘乙亡享仇仍仔仗仙令仰仿企伍伯估伸似佈佔佛佳依侵促俊俗保修俱倆倉倍倦偉偏偵傅傍催傲傳傷傻傾僅僑價儀億儘償優儲允充兇免兔入兼冊冠冤准凌凍凳划列初判制刺則削剪副割創劇劣勇勉勝勞勢勤勵勸勿匯協博占印即卷厚厲及反叔取古另叨召叭史吊吐吞否吩含吸吻呈呼命咐咬咱哇員哦哲唉售唯善喇喉喊喔喪喲嗨嘍嘗嘮嘿噢噪噴噸嚇嚐嚨固圈圍團圾均坪垃型埋域執培基堂堅堆塌塗塞墊壁壓壯壽夕夢夫央失夾奈奏奔奪奮妙妝妥妻姑委姻威娃娘娛娶婆婦媳嫁嫂嫌嬰孕存孝孤孫宅守宗官宣宴宵寂密寞寧審寬寶寸寺射專尊尋導尖尾尿屁屆展屜層屬岸峰島峽崇州巨巷巾帝帥席帳幅幕幢幣幸幹幻幽序府座庫廟廠廢延引弱強彈彎彩彼待律復循微徵徹忍志怒怖性怨恐恢恨悄悉悔悟悲惜惠惡惱惹愁愉愧慌慎慕慘慚慧慮慰憐憑憤憶懇懶懷懸戀戒戚截戰戲扁扇扣扮扯扶批承技抄抓投抖抗折披抵抹押拆拌拒拓拔拖招括拳拼拾持按挑挖挫挺捉捏捐捕捧捨捲授掌掏採探控掩揀描插揚揮援損搓搖搞搭摔摟摸撈撐撕撞撥撲撿擁擋操據擱擲擴擺擾攀攝攤政效敗敬敲敵斜斥斷於施族旗既旦昏映晨普晰智暈暗暫暴曉曬曲曾朗朝李材村枉析枕某染柔柴格桃案桶梅梨械棄棉棋棟植椒榜榮構槍標模橫檔櫃欄權欠欣欺款歇止此武歧歪歷殊殖毒毫毯氛氧汗江污沉沖治沿泛泡波泥洞派浪浮浴浸液淇淋淘淚混減渡測港湊源溜溝溫溼滅滴滾漠漫漲漸漿潑潔潤潮澆激濃濕濟濾瀑灘灰災炒炮烈煙煤熊熬燃燙營燭爆爛爭版牌牢牲牽犧犯狀狂狼猛猴獄獅獎獨獲獸獻率王玫玻珍琴瑰璃瓷甚甩田甲申略番異疏疑疲疾症痕瘋癢登皂皇盆益盜盡監盯盲盼盾省眠眾睜督瞎瞧矛矩砍砲砸硬碌碎碰磁磅磨礎礙示社祕祖禁禍福禿秀私秘秩移稅稍稱積穩穫突窄窮竟端競竹符筋筒策箭範篇築簽籍粉粒粗粘粥糊糟糧系糾純紛素索紫終組絕絡絲綜維線緣編緩縫縮繁織繞繩繳缺罐罪置罰罷群羨義翅翻者而耍耐耗耽聖聘聚聯職肅肌肖肝股肥肩肺胎胞脅脆脖脹脾腐腫腰腸膀膏膚膨膽臟臥臨至致臺舅舌航般艘良菌菠華菸落葉葬蓄蓋蔬蕉薄薦薪藏藝虎虛虧蚊蛇蜂蜜蝦融螞蟲蟻蠟蠶血術衛衡袍袖裁裂裕補裳裹製覆規覽角觸訂訊訓託訝診註証評詩詳誇誌誕誼諷謂謙證譯讚豆象貌貝財貢貧貸貿賀賞賠質賭賺購贈贊贏赴趁趟跌距跡跨跪踩蹈蹟蹲躁躍躬躲軍軟載輔輩輪辣辭農迅返迫迷追退逃透逐途逗逛速造逢逼達違遞適遭遵遷避邀郎配醉醒醜野量針釣鈔鈕銅銳銷鋪鋼鍊鍋鍛鍵鎖鐵鑽閃閉閒閱闆闊闖防阻陌降限陣陳陶隊階隔際障雀雄集雕雜震霧露靈靠革鞠鞭項順頗顆額類顯飄飼飾養餘饅駕駛騙騷驕驗驚骨骯鬆鬍鬥鬼魂魅鮮鴨鵝鹹麥黏默黨鼓齡龍'.decode("utf-8")

def get_top4():
  return '丐丘串丹乃乒乓乞乳予于井亞亦京仁仕伏伙伴伺佇佑佩併侈侮侶俏俘倘倚倡倫偶傢債僱儉儒兀兌兢兵冥凋凝凡刊刑券剎剔剖剝劑勁勃勒募勻勾匆匹匾卉卓卦卵叢吉君吭呆咕咦哀哄哩哺哼唇唐唷啞啟啼喘喚喻嗓嗜嗦嘀嘆嘻嚮嚷囉囊囑坊坦垂堪堵塑塔塵墅墓墟墨墮墳壇壟壤壺夥奉契奠奢奧奴妄妒妨姆姿媒嫉孔宇宏宙宮宰寡寢寵尚屈屍屎履岩峙峭崖崗崩嶄嶼巡幟干幼庸廂廉廊廓弊弓彌彗彙徑徒忌忠怠恍恩恰恿悅悠患悶惋惑惕惚惦惰惶愚慈慨慫慷憂憊憋憧憬憲憾懈懊懦懼扎扛扭抉抑拋拐挨挪振挽捆捷掀掘掙措揉揍揪揭搏搜摧摯撒撓撤撫撮撰擅擊擎擬攔攪攻敏敘敝敷斧斯旋旨旬旺昂昆昔晃晉晶暢暨曝曠朽松枚枷柄柱柳株核栽梭梳棍棺楣榷樑樸櫻欸欽歎歸歹殘殼殿毀毅氏氓汰汲沐沫沮沸沼沾泉泌津洩洪洽涉涕涵淆淒淪淹添渠渾湧溉溪溶滋滯滲漁漆漏潛潢潰潺澈澤濁濫濺瀟灌灑灸炎烊烏焦焰煌煎煞燕燥燦爍爐爽爾牧狐狠狩狹猖猶獗獵珠瑕瑣瓣瓦甦甭畝畸疊疙疫疵痰瘟瘩療癌癮皆皺盛盞盟眉睦睹瞞瞪瞬矚碑碩磋磚礦祀祥祭禦稚稠稻穎穴窩窯竊竭篷簇籠籤籬籲糙糞紊紋納紡綁綱綿緒緝締緻縛縱繡繪繫纖罩署罹翁翌翔翠翹耀耕肪胃胡胳胸脂脈腔膊膠膩臘艦艱艶芒芽苗苛若茂茫荒莊萎蒙蒸蒼蓬蔑蔓蔽蕩薯藉藩虐虔虜蛙蝕蝴蝶蝸蟬蠅蠢蠻衍衝衰衷袱裔襲詢誓誘誦誨諧諸諾謀謊謎謠謹譜譬譽谷豁豔豪豫販貪貫貶賂賃賄賊賓賜賢賤賦賴贓趨趴踐踴蹤蹺軌軸輝輯輻輿轎轟辜辨辯辰辱述迴逍逝逮逾遙遜遣遮遺遼邁邏酌酗酬酷醇醞釀釘鈍鈣鈴鈾鉅銘鋁鋒鋤錫鎮鑲鑼閡閣閥闢陡陵陷隆隧隱隸雅雇雷霜靴鞏頂頌頑頒顛顫飢饒饞馴駐駝駱騰驅驟驢髓髦鬱魁魄魔魯鯨鳴鴉鴿鷹黎鼠龐龜'.decode("utf-8")


if __name__ == "__main__":
  print "Don't run me.  I'm a plugin!"

else:
  mw.addHook('init', init_hook)
  print 'HanziStats plugin loaded'

