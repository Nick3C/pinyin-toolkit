#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import string
import getpass
import unicodedata

import pinyin

"""
Is the current user a developer?
"""
#Check for users
# on macos you can type echo %username% to get this but it doesn't work on windows.
#def debugmode():
#    return getpass.getuser() in ["mbolingbroke","Nick"]

# Uncomment the following two lines to force developer mode
def debugmode():
   return True



"""
Suppress exceptions originating from execution of the given action, unless
the current user is a developer
"""
def suppressexceptions(action):
    if debugmode():
        # Don't suppress exceptions for the developers!
        action()
    else:
        try:
            action()
        except:
            pass

"""
Utility function that reports whether a string consists of a single punctuation
character
"""
def ispunctuation(what):
    return len(what) == 1 and unicodedata.category(unicode(what[0])) == 'Po';


"""
Reports the absolute directory name that the pinyin/ directory has at runtime
"""
def executiondir():
    try:
        return os.path.dirname(os.path.realpath( __file__ ))
    except NameError:
        # That doesn't work in the interactive shell, so let's do this instead:
        return os.path.dirname(sys._getframe(1).f_code.co_filename)

"""
Reports whether we can write a particular path. Just deals with permissions, so may
throw IOError if e.g. the directory the file was in doesn't exist.
"""
def canwriteto(path):
    try:
        f = open(path, 'w')
        f.close()
        
        return True
    except IOError, e:
        # Check that the IO error occurs because of a permissions issue
        if e.errno == 13:
            return False
        else:
            raise e

"""
Creates the supplied directory if it doesn't exist.
"""
def ensuredirexists(dirpath):
    if not(os.path.exists(dirpath)):
        os.makedirs(dirpath)

"""
Find the hex-format MD5 digest of the input.
"""
def md5(what):
    # Try hashlib first, as it's the newer library (Python 2.5 or later)
    try:
        import hashlib
        hashlib.md5(what).hexdigest()
    except ImportError:
        pass
    
    # Fall back on md5, the deprecated equivalent that Anki comes with
    import md5
    return md5.new(what).hexdigest()

"""
Reports whethere this token is the pinyin for 'r5' which often occurs at the end of words.
"""
def iserhuapinyintoken(token):
    return type(token) == pinyin.Pinyin and token.word == 'r' and token.tone == 5

"""
Lazy evaluation: defer evaluation of the function, then cache the result.
"""
class Thunk(object):
    def __init__(self, function):
        # Need to initialize all fields or __getattr__ gets a look at them!
        self.__called = False
        self.__result = None
        self.__function = function
    
    def __call__(self):
        if self.__called:
            return self.__result
        
        self.__called = True
        self.__result = self.__function()
        self.__function = None # For garbage collection
        return self.__result

    # Transparent proxying of access onto the thing inside the thunk!
    def __getattr__(self, name):
        return getattr(self.__call__(), name)

"""
Use the regex to parse the text, alternately yielding match objects and strings
"""
def regexparse(regex, text):
    i = 0
    while i < len(text):
        match = regex.search(text, i)
        
        if match:
            # Yield the text up until this point
            if i != match.start():
                yield (False, text[i:match.start()])
            
            # Got a matched fragment of text
            yield (True, match)
            
            # Continue from the end of the match
            if match.end() == i:
                yield (False, text[i])
                i = match.end() + 1
            else:
                i = match.end()
        else:
            # Yield the text up until the end
            if i != len(text) - 1:
                yield (False, text[i:])
            return

if __name__=='__main__':
    import unittest
    import re
    
    class ThunkTest(unittest.TestCase):
        def testCall(self):
            self.assertEquals(Thunk(lambda: 5)(), 5)
        
        def testTransparency(self):
            self.assertEquals(Thunk(lambda: "hello!").rstrip("!"), "hello")
    
    class RegexParseTest(unittest.TestCase):
        def testParseSimple(self):
            self.assertEquals(self.parse(re.compile("foo"), "foo bar foo bar"),
                              [(True, "foo"), (False, " bar "), (True, "foo"), (False, " bar")])
        
        def testParseEmpty(self):
            self.assertEquals(self.parse(re.compile(""), "abc"),
                              [(True, ""), (False, "a"), (True, ""), (False, "b"), (True, ""), (False, "c")])
        
        # Test helpers
        def parse(self, re, text):
            result = []
            for ismatch, thing in regexparse(re, text):
                if ismatch:
                    result.append((ismatch, thing.group(0)))
                else:
                    result.append((ismatch, thing))
            
            return result

    unittest.main()