#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import string
import getpass
import unicodedata

import pinyin

"""
Suppress exceptions originating from execution of the given action, unless
the current user is a developer
"""
def suppressexceptions(action):
    if getpass.getuser() in ["mbolingbroke"]:
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