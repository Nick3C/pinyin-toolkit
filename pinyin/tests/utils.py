# -*- coding: utf-8 -*-

import unittest

from pinyin.utils import *


class LetTest(unittest.TestCase):
    def testLet(self):
        self.assertEquals(let(1, "hello", lambda x, y: str(x) + y), "1hello")

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
    
    def testSortedBySecond(self):
        self.assertEquals(sorted([(5, "1"), (2, "4"), (3, "2"), (1, "5"), (4, "3")], bySecond), [(5, "1"), (3, "2"), (4, "3"), (2, "4"), (1, "5")])

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
    
    def testParseNeedStuffAtEnd(self):
        self.assertEquals(self.parse(re.compile("foo"), "foo foo, foo!"),
                          [(True, "foo"), (False, " "), (True, "foo"), (False, ", "), (True, "foo"), (False, "!")])
    
    # Test helpers
    def parse(self, re, text):
        result = []
        for ismatch, thing in regexparse(re, text):
            if ismatch:
                result.append((ismatch, thing.group(0)))
            else:
                result.append((ismatch, thing))
        
        return result

class FactoryDictTest(unittest.TestCase):
    def testFactory(self):
        dict = FactoryDict(lambda x: x + 1)
        self.assertEquals(dict[3], 4)
    
    def testNormalOperation(self):
        dict = FactoryDict(lambda x: x + 1)
        
        dict[2] = "Hello"
        self.assertEquals(dict[2], "Hello")
        
        dict[3] = "Bye"
        self.assertEquals(dict[2], "Hello")
        self.assertEquals(dict[3], "Bye")