#!/usr/bin/python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
########################################################################
###                   Mandarin-Chinese Pinyin Toolkit                ### 
########################################################################
# A Plugin for the Anki Spaced Repition software http://ichi2.net/anki/

# Version Details:
pinyin_toolkit="0.05 dev 4.3"
CCDict_Ver="2009-05-29T05:46:28Z" # [n=84885] http://www.mdbg.net/chindict/chindict.php?page=cc-cedict
HanDeDict_Ver="Sat May 30 00:20:38 2009" # [n=169500] http://www.chinaboard.de/chinesisch_deutsch.php?mode=dl&w=8
CFDICT_Ver="Wed Jan 21 01:49:53 2009" # [n=593] http://www.chinaboard.de/fr/cfdict.php?mode=dl&w=8
dictlanguage="en" # Sets language
# full support for: "en" (english) and "de" (German)
#     Note that there are some important differences between handedict and cc-cedict (Measures Words, Simp-Trad swap, etc)
# partial support for: "fr" (French) [CFDICT is still small but google translate will pick up the slack]
# google translate support for other languges (use language code: http://www.loc.gov/standards/iso639-2/php/code_list.php)


############### Settings Section ###############

### Options ###
# Can be either True or False
colorizePY=True 
tonify=True
DictionaryGeneration=True
FallBackOnGoogleTranslate=True
cochargen=True
audiogen=True
MWcutout=True # must have translate on (and be using a dictionary version)

# seperator for meaning dictionary entries
endictsep = "<br />"
# default is "<br />" obvious alternatives are: ", " or "; "

# What type of audio files are you using?
audioextension = ".mp3" 

# Field Settings (should match your model) PY_TK will guess defaults if not presen #
expressionField = "Chinese"
readingField = "Pinyin"
meaningField ="English"
audioField = "Audio"
colorField = "Color"
MWField = "MW"

# The following line controls which model tag is used (it must match your deck)
# You should not need to change this setting
modelTag = "Mandarin"

############### End of Settings Section ###############

import sys
import os

import re
from ankiqt import mw
import anki
from pinyin import pinyinfetcher
from anki.hooks import addHook, removeHook
from anki.features.chinese import onFocusLost as oldHook

import urllib,urllib2 # for google translate

#define the convertor models as per options above
converterPY = pinyinfetcher.PinyinFetcher(colorizePY,tonify)

if(DictionaryGeneration):
    converterENG = pinyinfetcher.PinyinFetcher(False,False,True,False,dictlanguage)
else:
    converterENG = None
    
if(audiogen):
    converterAudio = pinyinfetcher.PinyinFetcher(False,False,False,True)
else:
    converterAudio = None

if(cochargen):
    converterColChar = pinyinfetcher.PinyinFetcher(True)
else:
    converterColChar = None  
    
def onFocusLost(fact, field):
    if field.name != expressionField:
        return
    if not anki.utils.findTag(modelTag, fact.model.tags):
        return
    newinput=field.value
    try:
        """
        # Check user specified fields exist, if not then default to standard usage
        if not (expressionField in currentCard.fact):
            expressionField = 'Expression'
        if not (readingField in currentCard.fact):
            readingField = 'Reading'
        if not (meaningField in currentCard.fact):
            readingField = 'Meaning'
        if not (colorField in currentCard.fact):
            colorField = 'Color'
        if not (audioField in currentCard.fact):
            colorField = 'Audio'
        """


        if not fact[expressionField]:
            fact[readingField] = u""
            fact[meaningField] = u""
            fact[colorField] = u""
            audiolen=len(fact[audioField])
            # DEBUGME - add a more rigerous check on audio fields here (having problems with ratio based approach)
            if audiolen < 40: #
                fact[audioField] = u""
            return
        if not fact[readingField] :
            tmp = converterPY.getPinyin(newinput,False)
            if tmp != newinput:
                fact[readingField] = tmp.lower()
        if not fact[meaningField]:
            tmp = converterENG.getPinyin(newinput,True,False,False,dictlanguage).replace("CL:","MW:")
             
                        
            if (MWcutout): # cut measure word and paste into MW field
                MWpos = tmp.find("MW:")
                if MWpos != -1:
                    tmplen = len(tmp)
                    MWcut = tmp[MWpos+5:tmplen].replace("["," - ").replace("]","")
                    fact[MWField] = MWcut

                    tmp=tmp[:MWpos-1]
            
            tmp=tmp.replace("/",endictsep) #convert dictionary spacers and return  
            
            if tmp == "":
                if (FallBackOnGoogleTranslate):
                    tmp=gTrans(newinput)
            if tmp != newinput:
                fact[meaningField] = tmp                     
        if not fact[audioField]:
            tmp = converterAudio.getPinyin(newinput,False,False,False,audioextension)
            if tmp != newinput:
                fact[audioField] = tmp.lower()
        if not fact[colorField]:
            tmp = converterColChar.getPinyin(newinput,False,True)
            if tmp != newinput:
                fact[colorField] = tmp 
        return
    except:
        return 


#gtrans ######################################################################
def gTrans(src):
    url="http://translate.google.com/translate_a/t?client=t&text=%s&sl=%s&tl=%s"%(urllib.quote(src.encode('utf-8')),'zh-CN',dictlanguage)
    con=urllib2.Request(url, headers={'User-Agent':'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'}, origin_req_host='http://translate.google.com')
    try:
        req=urllib2.urlopen(con)
    except urllib2.HTTPError, detail:
        return '<span style="color:gray">[Internet Error]</span>'
    except urllib2.URLError, detail:
        return '<span style="color:gray">[Internet Error]</span>'
    ret=U''
    for line in req:
        line=line.decode('utf-8').strip()
    ret=U' '.join( (ret,line) )
    ret = unicode(eval(ret),'utf8') + '<br /><span style="color:gray"><small>[Google Translate]</small></span>'
    return ret



removeHook('fact.focusLost', oldHook)
addHook('fact.focusLost', onFocusLost)
mw.registerPlugin("Mandarin Chinese Pinyin Toolkit", 4)

if __name__ == "__main__":
  print "This is a plugin for the Anki Spaced Repition learning system and cannot be run directly."
  print "Please donwload Anki from <http://ichi2.net/anki/>"