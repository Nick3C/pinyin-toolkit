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
Utility function that reports whether a string consists of a single punctuation
character
"""
def ispunctuation(what):
    return len(what) == 1 and unicodedata.category(unicode(what[0])) == 'Po';


"""
Reports the absolute directory name that the pinyin/ directory has at runtime
"""
def pinyindir():
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
        hashlib.md5(what).hexdigest()
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
Sorting combinator: sort by first element
"""
def byFirst(x, y):
    return cmp(x[0], y[0])

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

def urlescape(what):
    import urllib
    return urllib.quote(what.encode('utf-8'))

def striphtml(what):
    return re.sub('<(?!(?:a\s|/a|!))[^>]*>', '', what)

def concat(what):
    return sum(what, [])

#
# Color conversion appropriated from <http://code.activestate.com/recipes/576554/>
# We can replace this with a use of the colorsys module when Anki uses Python 2.6
#

def hsvToRGB(h, s, v):
    """Convert HSV color space to RGB color space
    
    @param h: Hue
    @param s: Saturation
    @param v: Value
    return (r, g, b)  
    """
    import math
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
    v = maxc
    if maxc == 0.0:
        s = 0.0
    else:
        s = 1 - (minc * 1.0 / maxc)
    return (h, s, v)

#
# End code from ActiveState recipe
#

if __name__=='__main__':
    import unittest
    
    class ConcatTest(unittest.TestCase):
        def testConcatNothing(self):
            self.assertEquals(concat([]), [])
            self.assertEquals(concat([[], []]), [])
        
        def testConcat(self):
            self.assertEquals(concat([[1, 2], [3, 4], [], [5]]), [1, 2, 3, 4, 5])
    
    class UrlEscapeTest(unittest.TestCase):
        def testEscapeUrlEncode(self):
            self.assertEquals(urlescape("Hello World"), "Hello%20World")
        
        def testEscapeUTF8(self):
            self.assertEquals(urlescape(u"你"), "%E4%BD%A0")
    
    class StripHtmlTest(unittest.TestCase):
        def testStripNothingFromText(self):
            self.assertEquals(striphtml("Hello World"), "Hello World")
        
        def testStripTags(self):
            self.assertEquals(striphtml("Hello <b>World</b>"), "Hello World")
    
    class CumulativeTest(unittest.TestCase):
        def testCumulativeEmpty(self):
            self.assertEquals(list(cumulative([])), [])
            
        def testCumulative(self):
            self.assertEquals(list(cumulative([1, 2, 3, 2, 1])), [1, 3, 6, 8, 9])
    
    class SortingTest(unittest.TestCase):
        def testSortedByFirst(self):
            self.assertEquals(sorted([(5, "1"), (2, "4"), (3, "2"), (1, "5"), (4, "3")], byFirst), [(1, "5"), (2, "4"), (3, "2"), (4, "3"), (5, "1")])
        
        def testSortedInReverse(self):
            self.assertEquals(sorted([5, 2, 3, 1, 4], inReverse()), [5, 4, 3, 2, 1])
            self.assertEquals(sorted([5, 2, 3, 1, 4], inReverse(inReverse())), [1, 2, 3, 4, 5])
        
        def testSortedLexically(self):
            self.assertEquals(sorted([(3, 2), (1, 2), (1, 1), (3, 1), (2, 0)], lexically()), [(1, 1), (1, 2), (2, 0), (3, 1), (3, 2)])
            self.assertEquals(sorted([(3, 2), (1, 2), (1, 1), (3, 1), (2, 0)], lexically(inReverse())), [(3, 1), (3, 2), (2, 0), (1, 1), (1, 2)])
            self.assertEquals(sorted([(3, 2), (1, 2), (1, 1), (3, 1), (2, 0)], lexically(inReverse(), inReverse())), [(3, 2), (3, 1), (2, 0), (1, 2), (1, 1)])
    
    class HeadOrTest(unittest.TestCase):
        def testHeadOrNonEmpty(self):
            self.assertEquals(heador([1], "Another"), 1)
            self.assertEquals(heador([1, 2], "Another"), 1)

        def testHeadOrEmpty(self):
            self.assertEquals(heador([], "Another"), "Another")
    
    class HtmlColorTest(unittest.TestCase):
        def testParseBadLength(self):
            self.assertRaises(ValueError, lambda: parseHtmlColor(""))
            self.assertRaises(ValueError, lambda: parseHtmlColor("#aabbc"))
            self.assertRaises(ValueError, lambda: parseHtmlColor("#aabbccd"))
        
        def testParseBadStart(self):
            self.assertRaises(ValueError, lambda: parseHtmlColor("?aabbcc"))
        
        def testParseCorrectly(self):
            self.assertEquals(parseHtmlColor("#0156af"), (1, 86, 175))
    
        def testToHtmlColor(self):
            self.assertEquals(toHtmlColor(1, 2, 3), "#010203")
            self.assertEquals(toHtmlColor(1, 86, 175), "#0156af")
    
    class MkdirFallbackTest(unittest.TestCase):
        def testDirectoryForNameThatIsFree(self):
            def do(path):
                self.assertEquals(mkdirfallback(path, "Hello"), os.path.join(path, "Hello"))
    
            withtempdir(do)

        def testDirectoryForNameThatIsNotFree(self):
            def do(path):
                os.mkdir(os.path.join(path, "Hello"))
                self.assertEquals(mkdirfallback(path, "Hello"), os.path.join(path, "Hello 1"))
    
            withtempdir(do)

        def testDirectoryForNameHigherNumbers(self):
            def do(path):
                os.mkdir(os.path.join(path, "Hello"))
                os.mkdir(os.path.join(path, "Hello 1"))
                os.mkdir(os.path.join(path, "Hello 2"))
                self.assertEquals(mkdirfallback(path, "Hello"), os.path.join(path, "Hello 3"))
    
            withtempdir(do)
    
    class TouchTest(unittest.TestCase):
        def testTouch(self):
            def do(path):
                filepath = os.path.join(path, "Dumb")
                
                self.assertFalse(os.path.exists(filepath))
                touch(filepath)
                self.assertTrue(os.path.exists(filepath))
            
            withtempdir(do)
    
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