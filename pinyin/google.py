#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib, urllib2

# NB: Pinyin Toolkit is expecting this to return a LIST of meanings, when it eventually works
def googletranslate(src, language):
    url = "http://translate.google.com/translate_a/t?client=t&text=%s&sl=%s&tl=%s"%(urllib.quote(src.encode('utf-8')), 'zh-CN', language)
    con = urllib2.Request(url, headers={'User-Agent':'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'}, origin_req_host='http://translate.google.com')
    try:
        request = urllib2.urlopen(con)
    except urllib2.HTTPError, detail:
        return '<span style="color:gray">[Internet Error]</span>'
    except urllib2.URLError, detail:
        return '<span style="color:gray">[Internet Error]</span>'
    
    # ?? Doesn't work at all. Not sure what is intended here.
    ret = u''
    for line in request:
        line = line.decode('utf-8').strip()
    ret = u' '.join( (ret, line) )
    ret = unicode(eval(ret),'utf8') + '<br /><span style="color:gray"><small>[Google Translate]</small></span>'
    return ret


if __name__ == "__main__":
    import unittest
    
    class GoogleTranslateTest(unittest.TestCase):
        def testTranslate(self):
            self.assertEquals(googletranslate(u"你好", "en"), "")
    
    unittest.main()