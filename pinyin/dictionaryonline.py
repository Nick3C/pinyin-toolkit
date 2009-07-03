#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import re

from pinyin import *
from logger import log
import utils

# This module will takes a phrase and passes it to online services for translation
# For now this modle provides support for google translate. In the future more dictionaries may be added.


# Translate the parsed text from Chinese into target language using google translate:
def gTrans(query, destlanguage='en', prompterror=True):
    log.info("Using Google translate to determine the unknown translation of %s", query)

    # No meanings if we don't have a query
    if query == None:
        return None
    
    # No meanings if our query is blank after stripping HTML out
    query = utils.striphtml(query)
    if query.strip() == u"":
        return None

    try:
        # Return the meanings (or lack of them) directly
        return lookup(query, destlanguage)
    except urllib2.URLError, e:
        # The only 'meaning' should be an error telling the user that there was some problem
        log.exception("Error while trying to obtain Google response")
        if (prompterror):
            return [[Word(Text('<span style="color:gray">[Internet Error]</span>'))]]
        else:
            return
    except ValueError, e:
        # Not an internet problem
        log.exception("Error while parsing Google response: %s" % repr(literal))
        if (prompterror):
            return [[Word(Text('<span style="color:gray">[Error In Google Translate Response]</span>'))]]
        else:
            return

# This function will send a sample query to Google Translate and return true or false depending on success
# It is used to determine connectivity for the Anki session (and thus whether Pinyin Toolkit should use online services or not)
def gCheck(destlanguage='en'):
    try:
        lookup(u"好", destlanguage)
        return True
    except urllib2.URLError:
        return False
    except ValueError:
        # Arguably could return True here, because it's not that the website is offline
        return False

# The lookup function is based on code from the Chinese Example Sentence Plugin by <aaron@lamelion.com>
def lookup(query, destlanguage):
    # Set up URL
    url = "http://translate.google.com/translate_a/t?client=t&text=%s&sl=%s&tl=%s" % (utils.urlescape(query), 'zh-CN', destlanguage)
    con = urllib2.Request(url, headers={'User-Agent':'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'}, origin_req_host='http://translate.google.com')
    
    # Open the connection
    log.info("Issuing Google query for %s to %s", query, url)
    req = urllib2.urlopen(con)
    
    # Build the result literal from the request
    literal = u""
    for line in req:
        literal += line.decode('utf-8')
        
    # Parse the response:
    try:
        log.info("Parsing response %s from Google", literal)
        result = parsegoogleresponse(literal)
    except ValueError, e:
        # Give the exception a more precise error message for debugging
        raise ValueError("Error while parsing translation response from Google")
    
    # What sort of result did we get?
    if isinstance(result, basestring):
        if result == query:
            # The result was, unhelpfully, what we queried. Give up:
            return None
        else:
            # Simple strings can be returned directly
            return [[Word(Text(result))]]
    elif isinstance(result, list):
        # Otherwise, we get a result like this:
        # ["Well",
        #   [
        #     ["verb","like","love"],
        #     ["adjective","good"],
        #     ["adverb","fine","OK","okay","okey","okey dokey","well"],
        #     ["interjection","OK!","okay!","okey!"]
        #   ]
        # ]
        try:
            return [[Word(Text(result[0]))]] + [[Word(Text(definition[0].capitalize() + ": " + ", ".join(definition[1:])))] for definition in result[1]]
        except IndexError:
            raise ValueError("Result %s from Google Translate looked like a definition but was not in the expected format" % result)
    else:
        # Haven't seen any other case in the wild
        raise ValueError("Couldn't deal with the correctly-parsed response %s from Google" % result)

def parsegoogleresponse(response):
    # This code is basically a hand-rolled (and rather specialised) LL parser
    # for the kinds of strings we get back from Google Translate. We can deal with:
    #  * String literals (with escaping) of the form "foo\tbar", possibly containing Unicode
    #  * Numeric literals (returned as longs)
    #  * List literals
    
    itemseperatorregex = re.compile('\\s*,')
    listendregex = re.compile('\\s*\\]')
    
    # Utility to consume from the string using the regex and return the new string if successful
    def munch(regex, what):
        match = regex.match(what)
        if match:
            return what[match.end():]
        else:
            return None
    
    def stringtoken(match, what):
        # Remove escape characters from the captured string with eval - nasty!
        string = eval(u'u"%s"' % match.group(1))
        return string, what
    
    def numbertoken(match, what):
        return long(match.group(0)), what
    
    def listtoken(match, what):
        list = []
        while True:
            # Process this list item
            item, what = parse(what)
            list.append(item)
            
            # End of item - must be followed by a comma or closing bracket
            whataftercomma = munch(itemseperatorregex, what)
            if whataftercomma is None:
                # No comma - must be list end
                what = munch(listendregex, what)
                if what is None:
                    # No list end - very confusing!
                    raise ValueError("Unexpected end of list with no closing bracket")
                else:
                    # End of list: continue after the closing bracket
                    return list, what
            else:
                # Comma: expect another item, so continue after the comma
                what = whataftercomma
    
    def whitespacetoken(match, what):
        return parse(what)
    
    # Action table keyed off regular expressions.  Matched top to bottom against
    # the current string, with the corresponding token handler fired if the regex
    # can deal with it.
    actions = [
        (re.compile('"((?:[^\\\\"]|\\\\.)*)"'), stringtoken),
        (re.compile('-?[0-9]+'), numbertoken),
        (re.compile('\\['), listtoken),
        (re.compile('\\s+'), whitespacetoken)
      ]
    
    # Parse loop using the action table
    def parse(what):
        # Match processors from top to bottom
        for regex, processor in actions:
            # Run processor if the regular expression matches
            match = regex.match(what)
            if match:
                return processor(match, what[match.end():])
        
        raise ValueError("Couldn't parse %s" % repr(what))
    
    # Use the constructed action table to parse the supplied string
    value, rest = parse(response)
    if len(rest) != 0:
        raise ValueError("Unexpected trailing characters %s" % repr(rest))
    else:
        return value


################################################################################
#Indicators
# Future interest in having icons above the facteditor representing various dictionaries
# Light up red/green indicators show if the entry is in the dictionary or not
# Can click-through to access online dictionary


################################################################################
# Future plans to impliment entries to CC-CEDICT, HanDeDict, and CFDICT from Anki.

# def submitSelector(self, Hanzi, Pinyin, language, translation):
#     log.info("User is attempting to submit an entry for %s [%s] to the %s dictionary", Hanzi, Pinyin, language)
# 
#     if language == "en":
#         submitCEDICT( Hanzi, Pinyin, translation) 
#     else:
#         log.warn("No %s dictionary available to submit entry to", language)
# 
# 
#     
# 
# def submitCEDICT(self, Hanzi, Pinyin, English ):
#     # Add function to use google translate to lookup traditional and simplfied (this way avoid handedict / ccedict swap problems
#     # need internet to make submittion anyway
#     hanziSimp = "" 
#     HanziTrad = ""
#     
#     # run hanzi thought lookup with tonify off to get pinyin + tones (need this format for CC-CEDICT) 
#     Pinyin = ""
#     
#     URL = "http://cc-cedict.org/editor/editor.php?return=&insertqueueentry_diff=+" + hanzisimp + "[" + pinyin +"]+/&popup=1&handler=InsertQueueEntry"


if __name__ == "__main__":
    import unittest
    
    class ParseGoogleResponseTest(unittest.TestCase):
        def testParseNumber(self):
            self.assertEquals(parsegoogleresponse('1'), 1L)
        
        def testParseNegativeNumber(self):
            self.assertEquals(parsegoogleresponse('-1'), -1L)
        
        def testParseString(self):
            self.assertEquals(parsegoogleresponse('"hello"'), "hello")
        
        def testParseStringWithEscapes(self):
            self.assertEquals(parsegoogleresponse('"hello\\t\\"world\\""'), 'hello\t"world"')
        
        def testParseUnicodeString(self):
            self.assertEquals(parsegoogleresponse(u'"好"'), u'好')
        
        def testParseList(self):
            self.assertEquals(parsegoogleresponse('[1, "hello", 10, "world", 1337]'), [1, "hello", 10, "world", 1337])
        
        def testParseListOfLists(self):
            self.assertEquals(parsegoogleresponse('[1, [2, [3, 4]], [5, 6]]'), [1, [2, [3, 4]], [5, 6]])
        
        def testParseWhitespace(self):
            self.assertEquals(parsegoogleresponse('[ 1    ,"hello",[10, "barr rr"],   "world"   , 1337 ]'), [1, "hello", [10, "barr rr"], "world", 1337])
        
        def testParseErrorIfTrailingStuff(self):
            self.assertRaises(ValueError, lambda: parsegoogleresponse('1 1'))
            self.assertRaises(ValueError, lambda: parsegoogleresponse('"hello" 1'))
            self.assertRaises(ValueError, lambda: parsegoogleresponse('[1] 1'))
        
        def testParseErrorIfUnknownCharacters(self):
            self.assertRaises(ValueError, lambda: parsegoogleresponse('{ "hello" }'))
        
        def testParseErrorIfListNotClosed(self):
            self.assertRaises(ValueError, lambda: parsegoogleresponse('[ "hello"'))
        
        def testParseErrorIfEmpty(self):
            self.assertRaises(ValueError, lambda: parsegoogleresponse(''))
    
    class GoogleTranslateTest(unittest.TestCase):
        def testTranslateNothing(self):
            self.assertEquals(gTrans(""), None)
        
        def testTranslateEnglish(self):
            self.assertEquals(gTrans(u"你好，你是我的朋友吗？"), [[Word(Text(u'Hello, You are my friend?'))]])
        
        def testTranslateFrench(self):
            self.assertEquals(gTrans(u"你好，你是我的朋友吗？", "fr"), [[Word(Text(u'Bonjour, Vous \xeates mon ami?'))]])
        
        def testTranslateIdentity(self):
            self.assertEquals(gTrans(u"canttranslatemefromchinese"), None)
        
        def testTranslateStripsHtml(self):
            self.assertEquals(gTrans(u"你好，你<b>是我的</b>朋友吗？"), [[Word(Text(u'Hello, You are my friend?'))]])
        
        def testTranslateDealsWithDefinition(self):
            self.assertEquals(gTrans(u"好"), [
                [Word(Text("Well"))],
                [Word(Text("Verb: like, love"))],
                [Word(Text("Adjective: good"))],
                [Word(Text("Adverb: fine, OK, okay, okey, okey dokey, well"))],
                [Word(Text("Interjection: OK!, okay!, okey!"))]
              ])
        
        def testCheck(self):
            self.assertEquals(gCheck(), True)
    
    unittest.main()