#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib, urllib2

# This module will takes a phrase and passes it to online services for translation
# For now this modle provides support for google translate. In the future more dictionaries may be added.


# Translate the parsed text from Chinese into target language using google translate
# The gTrans function is based on code the Chinese Example Sentence Plugin by aaron@lamelion.com
def gTrans(src=None,destlanguage='en'):
    if src == None: # if no query then return nothing
        return    
    # Set up URL query
    url="http://translate.google.com/translate_a/t?client=t&text=%s&sl=%s&tl=%s"%(urllib.quote(src.encode('utf-8')),'zh-CN',destlanguage)
    con=urllib2.Request(url, headers={'User-Agent':'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'}, origin_req_host='http://translate.google.com')
    # Set what the return messages will be on success & faliure
    succeed='<br /><span style="color:gray"><small>[Google Translate]</small></span>'
    oops='<span style="color:gray">[Internet Error]</span>'
    
    try:
        req=urllib2.urlopen(con)
    except urllib2.HTTPError, detail:
        return oops
    except urllib2.URLError, detail:
        return oops
    ret=U''
    for line in req:
        line=line.decode('utf-8').strip()
        ret+=line
    if ret !="":        # if a result is found then:
        ret += succeed  # append a notice that this is auto-translated text (so user knows it may contain mistakes)
    return ret 

# This function will parse a sample query through google translate and return true or false depending on success
# It is used to determine connectivity for the Anki session (and thus whether Pinyin Toolkit should use online services or not)
def gCheck(testphrase=u"这是一个网络试验",destlanguage="en"):
    url="http://translate.google.com/translate_a/t?client=t&text=%s&sl=%s&tl=%s"%(urllib.quote(testphrase.encode('utf-8')),'zh-CN',destlanguage)
    con=urllib2.Request(url, headers={'User-Agent':'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'}, origin_req_host='http://translate.google.com')
    try:
        req=urllib2.urlopen(con)
    except urllib2.HTTPError, detail:
        return False
    except urllib2.URLError, detail:
        return False
    return True
    

if __name__ == "__main__":
    import unittest
    
    class GoogleTranslateTest(unittest.TestCase):
        def testTranslate(self):
            self.assertEquals(googletranslate(u"你好，你是我的朋友吗？", "en"), "")
    
    unittest.main()