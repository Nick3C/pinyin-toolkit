#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import string
import getpass
import unicodedata

"""
Is the current user a developer?
"""
def debugmode():
    # Uncomment to force debug mode on:
    #return True
    
    # Uncomment to force debug mode off:
    #return False
    
    # A simple way that ordinary users can get extra logging:
    if os.path.exists(toolkitdir("enable-pinyin-toolkit-log.txt")):
        return True
    
    # Username as reported on Windows by typing into cmd:
    #   echo %USERNAME%
    #
    # Or your login name on OS X / Linux.
    return getpass.getuser().lower() in [user.lower() for user in ["mbolingbroke", "Nick"]]

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
            # NB: have to delay the import of logger because it depends on utils
            from logger import log
            log.exception("Had to suppress an exception")

"""
Utility function that reports whether a string consists only of punctuation character
"""
def ispunctuation(text):
    # NB: can't use "all" because it's not in Python 2.4 and below, which Anki uses
    for char in text:
        # For General_Category list see http://unicode.org/Public/UNIDATA/UCD.html
        # Po . , ' "
        # Pd -
        # Ps ( [
        # Pe ) ]
        if 'P' not in unicodedata.category(unicode(char)):
            return False
    
    return True

"""
Reports whether a string consists of only punctuation characters that should have a space added after them.
"""
def ispostspacedpunctuation(text):
    return text in [u"·", u"。", u".", u"，", u","]

"""
Reports whether a string consists of only punctuation characters that should have a space added before them.
"""
def isprespacedpunctuation(text):
    return text == u"·"

"""
Turns the empty string into None and leaves everything else alone.
"""
def zapempty(what):
    if what == "":
        return None
    else:
        return what

"""
Reports the absolute directory name that the root toolkit directory has at runtime
"""
def toolkitdir(*components):
    try:
        return os.path.join(os.path.dirname(os.path.realpath( __file__ )), "..", *components)
    except NameError:
        # That doesn't work in the interactive shell, so let's do this instead:
        return os.path.join(os.path.dirname(sys._getframe(1).f_code.co_filename), "..", *components)

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
Create a directory in the specified path with the specified name, falling back on
that directory name with numeric suffixes if the name is not available.
"""
def mkdirfallback(path, name):
    import itertools
    
    # Keep trying longer names for the directory until one becomes available
    for n in itertools.count():
        if n == 0:
            proposeddir = os.path.join(path, name)
        else:
            proposeddir = os.path.join(path, name + " " + str(n))
        
        if not(os.path.exists(proposeddir)):
            # Claim this directory as the one we are after!
            os.mkdir(proposeddir)
            return proposeddir

"""
Given an action, creates a temporary directory and then feeds the action the full
path of that directory. Finishes by totally deleting the directory.
"""
def withtempdir(do):
    import tempfile, shutil
    
    # First, generate the temporary directory name
    tempdir = tempfile.mkdtemp()
    
    try:
        # Give the provided function an opportunity to use the directory
        do(tempdir)
    finally:        
        # Blast the temporary directory and its contents
        shutil.rmtree(tempdir)

"""
Create an empty file at the given location.
"""
def touch(where):
    open(where, 'w').close()

"""
Find the hex-format MD5 digest of the input.
"""
def md5(what):
    # Try hashlib first, as it's the newer library (Python 2.5 or later)
    try:
        import hashlib
        return hashlib.md5(what).hexdigest()
    except ImportError:
        pass
    
    # Fall back on md5, the deprecated equivalent that Anki comes with
    import md5
    return md5.new(what).hexdigest()

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
        elif self.__called is None:
            raise ValueError("A thunked computation entered a black hole")
        
        try:
            self.__called = None # Indicates that this thunk has become a black hole
            self.__result = self.__function()
            self.__called = True
        except Exception, e:
            from pinyin.logger import log
            # Thunked actions raising an exception is a massively bad idea, because there
            # is no way to know whose exception handler will be on the stack at the time we
            # realise it.  Nonetheless, our only recourse at this point is to let it bubble onwards...
            log.exception("A thunked action raised an exception! Letting it go through and hoping for the best...")
            raise
            
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
            yield (False, text[i:])
            return

"""
Returns the contents of a file: no muss, no fuss
"""
def filecontents(filepath):
    file = open(filepath, 'r')
    contents = file.read(-1)
    file.close()
    
    return contents

"""
Return the first item from the list or the other argument.
"""
def heador(list, orelse):
    if len(list) == 0:
        return orelse
    else:
        return list[0]

"""
Return the first argument if it is not None, otherwise return the second argument.
"""
def orelse(thing, alternative):
    if thing is not None:
        return thing
    else:
        return alternative

"""
Returns the left dictionary or set updated by the right one.
"""
def updated(leftdict, rightdict):
    leftdict.update(rightdict)
    return leftdict

"""
Pluralize the first noun with respect to the second count.
"""
def pluralize(what, count):
    if count == 1:
        return what
    else:
        return what + "s"

"""
Unzip a list.
"""
unzip = lambda l: tuple(zip(*l))

"""
Given a red, green and blue component of a color, return the corresponding HTML color.
"""
def toHtmlColor(r, g, b):
    toHex = lambda thing: ("%x" % thing).rjust(2, '0')
    return "#" + toHex(r) + toHex(g) + toHex(b) 

"""
Given a color in HTML format (#0156af), return the red, blue and green components as integers.
"""
def parseHtmlColor(color):
    if len(color) != 7:
        raise ValueError("HTML color %s has the wrong length" % color)
    
    if color[0:1] != '#':
        raise ValueError("HTML color %s does not begin with a #" % color)
    
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)

"""
Sorting combinator: sort using a projected quantity.
"""
def using(proj, how=cmp):
    return lambda x, y: how(proj(x), proj(y))

"""
Sorting combinator: sort by first element
"""
def byFirst(x, y):
    return cmp(x[0], y[0])

"""
Sorting combinator: sort by second element
"""
def bySecond(x, y):
    return cmp(x[1], y[1])

"""
Sorting combinator: reverse order:
"""
def inReverse(how=cmp):
    return lambda x, y: how(y, x)

"""
Sorting combinator: lexical order:
"""
def lexically(*hows):
    def do(x, y):
        # Compare items in the two values in order
        # TODO: deal with case where lengths differ?
        for n, (xitem, yitem) in enumerate(zip(x, y)):
            if n < len(hows):
                # Use a comparer if we have one
                how = hows[n]
            else:
                # Otherwise default to cmp
                how = cmp
            
            # Return a definitive answer from this element if we can get one
            res = how(xitem, yitem)
            if res != 0:
                return res
        
        # Indistinguishable!
        return 0

    return do

"""
Cumulative total iterator.
"""
def cumulative(sequence):
    sofar = 0
    for n in sequence:
        sofar = sofar + n
        yield sofar

def lstripexactly(what, fromwhat):
    if fromwhat[0:len(what)] == what:
        return fromwhat[len(what):]
    else:
        raise ValueError("Couldn't strip %r from %r" % (what, fromwhat))

def urlescape(what):
    import urllib
    return urllib.quote(what.encode('utf-8'))

def striphtml(what):
    return re.sub('<(?!(?:a\s|/a|!))[^>]*>', '', what)

def concat(what):
    return sum(what, [])

def splitat(what, n):
    if n > len(what):
        raise ValueError("You cannot splitat at a point later than the end of the string")
    return what[0:n], what[n:]

def seq(x, y):
    return y()

def inplacefilter(pred, list):
    for i in range(len(list), 0, -1):
        if not pred(list[i - 1]):
            del list[i - 1]

def first(f):
    def go(xy):
        x, y = xy
        return (f(x), y)

    return go
    
def second(f):
    def go(xy):
        x, y = xy
        return (x, f(y))
    
    return go

def cond(test, tb, fb):
    if test:
        return tb()
    else:
        return fb()

def intersperse(what, things):
    first = True
    result = []
    for thing in things:
        if not(first):
            result.append(what)
        result.append(thing)
        first = False
    
    return result

def substrings(text):
    for length in range(len(text), -1, -1):
        for i in range(0, len(text) - length):
            yield text[i:i+length+1]

def marklast(things):
    for i, thing in enumerate(things):
        yield (i == len(things) - 1), thing

if sys.version_info[0:2] < (2, 5):
    def all(xs):
        for x in xs:
            if not x:
                return False
    
        return True

    def any(xs):
        for x in xs:
            if x:
                return True
    
        return False

#
# Color conversion appropriated from <http://code.activestate.com/recipes/576554/>
# We can replace this with a use of the colorsys module when Anki uses Python 2.6
#
# NB: have slightly modified the routines so that V is returned between 0 and 1, like
# the H and S values already were.
#

def hsvToRGB(h, s, v):
    """Convert HSV color space to RGB color space
    
    @param h: Hue
    @param s: Saturation
    @param v: Value
    return (r, g, b)  
    """
    import math
    v = int(round(v * 255.0))
    hi = math.floor(h / 60.0) % 6
    f =  (h / 60.0) - math.floor(h / 60.0)
    p = v * (1.0 - s)
    q = v * (1.0 - (f*s))
    t = v * (1.0 - ((1.0 - f) * s))
    return {
        0: (v, t, p),
        1: (q, v, p),
        2: (p, v, t),
        3: (p, q, v),
        4: (t, p, v),
        5: (v, p, q),
    }[hi]

def rgbToHSV(r, g, b):
    """Convert RGB color space to HSV color space
    
    @param r: Red
    @param g: Green
    @param b: Blue
    return (h, s, v)  
    """
    maxc = max(r, g, b)
    minc = min(r, g, b)
    colorMap = {
        id(r): 'r',
        id(g): 'g',
        id(b): 'b'
    }
    if colorMap[id(maxc)] == colorMap[id(minc)]:
        h = 0
    elif colorMap[id(maxc)] == 'r':
        h = ((g - b) * 60.0 / (maxc - minc)) % 360
    elif colorMap[id(maxc)] == 'g':
        h = ((b - r) * 60.0 / (maxc - minc)) + 120
    elif colorMap[id(maxc)] == 'b':
        h = ((r - g) * 60.0 / (maxc - minc)) + 240
    v = (maxc / 255.0)
    if maxc == 0.0:
        s = 0.0
    else:
        s = 1 - (minc * 1.0 / maxc)
    return (h, s, v)

#
# End code from ActiveState recipe
#

def isosx():
    return sys.platform.lower().startswith("darwin")

def islinux():
    return sys.platform.lower().startswith("linux")

def isHanzi(char):
    # Originally based on anki.stats.isKanji
    if type(char) == str:
        return False
    
    import unicodedata

    try:
        return unicodedata.name(char).find('CJK UNIFIED IDEOGRAPH') >= 0
    except ValueError:
        # A control character
        return False

class FactoryDict(dict):
    def __init__(self, factory, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.factory = factory
    
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            # Use the factory to build an item
            value = self.factory(key)
            self[key] = value
            return value

"""
Monadic bind in the Maybe monad (embedded into Python 'None's)
"""
def bind_none(mx, f):
    if mx:
        return f(mx)
    else:
        return None

def let(*stuff):
    return stuff[-1](*(stuff[:-1]))
