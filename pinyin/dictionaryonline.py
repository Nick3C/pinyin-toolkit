#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib, urllib2

from logger import log

# This module will takes a phrase and passes it to online services for translation
# For now this modle provides support for google translate. In the future more dictionaries may be added.


# Translate the parsed text from Chinese into target language using google translate:
def gTrans(query, destlanguage='en'):
    if query == None or query.strip() == u"":
        # No meanings if we don't have a query
        return []

    result = lookup(query, destlanguage)
    if result:
        # The only meaning is the result with the source of the meaning
        return [result + '<br /><span style="color:gray"><small>[Google Translate]</small></span>']
    else:
        # The only meaning should be an error
        return ['<span style="color:gray">[Internet Error]</span>']

# This function will send a sample query to Google Translate and return true or false depending on success
# It is used to determine connectivity for the Anki session (and thus whether Pinyin Toolkit should use online services or not)
def gCheck(destlanguage='en'):
    return lookup("example", destlanguage) != None

# The lookup function is based on code from the Chinese Example Sentence Plugin by <aaron@lamelion.com>
def lookup(query, destlanguage):
    # Set up URL
    url = "http://translate.google.com/translate_a/t?client=t&text=%s&sl=%s&tl=%s" % (urllib.quote(query.encode('utf-8')), 'zh-CN', destlanguage)
    con = urllib2.Request(url, headers={'User-Agent':'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'}, origin_req_host='http://translate.google.com')
    
    # Open the connection
    log.info("Issuing Google query for %s to %s", query, url)
    try:
        req = urllib2.urlopen(con)
    except urllib2.HTTPError, detail:
        log.exception("HTTPError during request")
        return None
    except urllib2.URLError, detail:
        log.exception("URLError during request")
        return None
    
    # Build the result from the request
    result = u""
    for line in req:
        line = line.decode('utf-8').strip()
        result += line
    
    if result != "":
        # Non-empty result: use it as the meaning
        return result.strip('"')
    else:
        log.warn("Empty result from Google - unexpected behaviour!")
        return None

################################################################################
#Indicators
# Future interest in having icons above the facteditor representing various dictionaries
# Light up red/green indicators show if the entry is in the dictionary or not
# Can click-through to access online dictionary






################################################################################
# Future plans to impliment entries to CC-CEDICT, HanDeDict, and CFDICT from Anki.


def submitSelector(self, Hanzi, Pinyin, language, translation):
    log.info("User is attempting to submit an entry for %s [%s] to the %s dictionary", Hanzi, Pinyin, language)

    if language == "en":
        submitCEDICT( Hanzi, Pinyin, translation) 
    else:
        log.warn("No %s dictionary available to submit entry to", language)


    

def submitCEDICT(self, Hanzi, Pinyin, English ):
    # Add function to use google translate to lookup traditional and simplfied (this way avoid handedict / ccedict swap problems
    # need internet to make submittion anyway
    hanziSimp = "" 
    HanziTrad = ""
    
    # run hanzi thought lookup with tonify off to get pinyin + tones (need this format for CC-CEDICT) 
    Pinyin = ""
    
    URL = "http://cc-cedict.org/editor/editor.php?return=&insertqueueentry_diff=+" + hanzisimp + "[" + pinyin +"]+/&popup=1&handler=InsertQueueEntry"
    
    


if __name__ == "__main__":
    import unittest
    
    class GoogleTranslateTest(unittest.TestCase):
        def testTranslateNothing(self):
            self.assertEquals(gTrans(""), [])
        
        def testTranslateEnglish(self):
            self.assertEquals(gTrans(u"你好，你是我的朋友吗？"), [u'Hello, You are my friend?<br /><span style="color:gray"><small>[Google Translate]</small></span>'])
        
        def testTranslateFrench(self):
            self.assertEquals(gTrans(u"你好，你是我的朋友吗？", "fr"), [u'Bonjour, Vous \xeates mon ami?<br /><span style="color:gray"><small>[Google Translate]</small></span>'])
        
        def testCheck(self):
            self.assertEquals(gCheck(), True)
    
    unittest.main()