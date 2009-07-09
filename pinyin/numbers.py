#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dictionary
import pinyin
import utils

#
# These are the low-level functions that just convert between
# hanzi representing integers and Python integers
#

def parsemany(ofwhat):
    def inner(text):
        things = []
        while True:
            thing, text = ofwhat(text)
            if thing is None:
                return things, text
            
            things.append(thing)
    
    return inner

def parsedigit(text):
    if len(text) > 0 and text[0].isdigit():
        return text[0], text[1:]
    else:
        return None, text

parsedigits = lambda text: "".join(parsemany(parsedigit)(text))

digits = [u"零", u"一", u"二", u"三", u"四", u"五", u"六", u"七", u"八", u"九"]

# Parsing a single digit: returns a digit (or None) and the rest of the string
def parsehanzidigit(hanzi):
    for digit, digittext in enumerate(digits):
        if hanzi.startswith(digittext):
            return digit, hanzi[len(digittext):]
    
    return None, hanzi

parsehanzidigits = lambda text: "".join(parsemany(parsehanzidigit)(text))

magnitudes = list(enumerate([
    u"",     # units
    u"十",    # tens
    u"百",    # hundreds
    u"千",    # thousands
    u"万",    # ten-thousands
    u"十万",   # hundred thousand
    u"百万",   # 10^6
    u"千万",   # 10^7
    u"亿",    # 10^8
    u"十亿",   # 10^9
    u"百亿",   # 10^10
    u"千亿",   # 10^11
    u"兆",    # 10^12
    u"十兆",   # 10^13
    u"百兆",   # 10^14
    u"千兆"    # 10^15
  ]))

# Takes western numbers and converts them into Chinese characters so they can be use in the dictionary lookup
def numberashanzi(n):  
    if n < 10:
        # Special case: if we just have 0, return ling,
        # or the logic below will just return an empty string.
        # Likewise, for the number 1 - so we may as well
        # do this for all manifest digits.
        return digits[n]
    
    hanzi = u""
    needling = False
    for power, text in reversed(magnitudes):
        tenpower = pow(10, power)
        
        # This check will only have an effect the first time around the
        # loop: if the number turns out to be too big, return the Arabic
        if n >= 10 * tenpower:
            return unicode(n)
        
        # NB: use floor division instead of ``true division'' here
        digit = n // tenpower
        n = n % tenpower
        
        if digit == 0:
            # We record the fact that we need to insert a ling before the end
            # as long as there we already have some digits in the output
            if hanzi != u"":
                needling = True
            
            # Don't display anything in the string right now
            continue
        
        if digit == 1 and power < 3 and hanzi == u"":
            # We can omit the leading one for numbers on numbers 100 or less
            hanzi += text
            continue
        
        if needling:
            # Insert a ling marker before the digit
            hanzi += digits[0]
            needling = False
        
        hanzi += digits[digit] + text
    
    return hanzi

# Takes Chinese characters and attempts to convert them into an integer
def parsehanziasnumber(hanzi):
    # The only valid form for 0 is 'ling'
    if hanzi.startswith(digits[0]):
        return 0, hanzi[len(digits[0]):]
    
    # Special case for the irregular 'liang'
    if hanzi.startswith(u"两"):
        return 2, hanzi[len(u"两"):]
    
    # Main loop that parses the numeric text from the left
    number = 0
    for power, powertext in reversed(magnitudes):
        # Start off by trying to parse a digit
        digit, candidatehanzi = parsehanzidigit(hanzi)
        if digit is None:
            if power == 0:
                # Musn't make assumption about leading digit if we're on
                # the final magnitude, or we might get an extra 1
                continue
            else:
                # Assume the leading digit is 1 if we couldn't find one
                digit = 1
        
        # Zeroes tend to act as filler between things which really
        # contribute to the number. NB: also deals with ling by itself
        if digit == 0:
            hanzi = candidatehanzi
            continue
        
        # If the remaining stuff doesn't look like a power, move on to
        # the next order of magnitude to give that a chance
        if not(candidatehanzi.startswith(powertext)):
            continue
        
        # Starts with a power, so we can accumulate the resulting stuff
        hanzi = candidatehanzi[len(powertext):]
        number += digit * pow(10, power)
    
    # If we still have 0 in the accumulator at this point then there
    # was no valid number there at all
    if number == 0:
        number = None
    
    # Return the number and any remaining text
    return number, hanzi

#
# Higher level functions using the ability to go between Hanzi and integers
#

# TODO: currency support?
# TODO: the Western and Chinese parsers are substantially the same. Perhaps more code could be shared.

def parsewesternnumberlike(expression, integerhandler, decimalhandler, yearhandler, percenthandler, fractionhandler):
    # Every numberlike form starts with some leading digits
    leadingdigits, expression = parsemany(parsedigit)(expression)
    expression = expression.strip()
    
    # Ensure we managed to get at least some digits
    if len(leadingdigits) == 0:
        return None
    
    # If that's followed by a decimal seperator and some digits we
    # can generate a Chinese decimal reading
    if expression.startswith(".") or expression.startswith(u"。"):
        trailingdigits, expression = parsemany(parsedigit)(expression[1:])
        if len(trailingdigits) == 0 or expression.strip() != u"":
            # Something after the trailing digits that we don't understand
            # or we didn't get any digits after . at all
            return None
        
        return decimalhandler(leadingdigits, trailingdigits)
    
    # What suffixes the integer?
    if expression == u"":
        # No suffix, return as a straight number
        return integerhandler(leadingdigits)
    elif expression == u"年":
        # Followed by a nian, return as a year
        return yearhandler(leadingdigits)
    elif expression in [u"%", u"％"]:
        # Followed by a percentage symbol, return as a percentage
        return percenthandler(leadingdigits)
    elif expression.startswith(u"/") or expression.startswith(u"\\"):
        # Followed by a slash, so could be a fraction
        trailingdigits, expression = parsemany(parsedigit)(expression[1:])
        if len(trailingdigits) == 0 or expression.strip() != u"":
            # Something after the trailing digits that we don't understand
            # or we didn't get any digits after the slash at all
            return None
        
        return fractionhandler(leadingdigits, trailingdigits)
    else:
        # Unknown suffix, we have to give up for sanity
        return None

def parsechinesenumberlike(expression, integerhandler, decimalhandler, yearhandler, percenthandler, fractionhandler):
    # Every numberilke form starts with some leading digits
    leadingnumber, trailingexpression = parsehanziasnumber(expression)
    leadingwesterndigits = list(str(leadingnumber))
    
    # Ensure we managed to get at least some digits
    if leadingnumber is None:
        return None
    
    # If that's followed by a decimal seperator and some digits we
    # can generate a Chinese decimal meaning
    if trailingexpression.startswith(u"点"):
        trailingdigits, trailingexpression = parsemany(parsehanzidigit)(trailingexpression[len(u"点"):])
        if len(trailingdigits) == 0 or trailingexpression.strip() != u"":
            # Something after the trailing digits that we don't understand
            # or we didn't get any digits after . at all
            return None
        
        return decimalhandler(leadingwesterndigits, trailingdigits)
    
    # What suffixes the integer?
    if trailingexpression == u"":
        # No suffix, return as a straight number
        return integerhandler(leadingwesterndigits)
    elif trailingexpression.startswith(u"分之"):
        # A fraction! Get the numerator
        trailingnumber, trailingexpression = parsehanziasnumber(trailingexpression[len(u"分之"):])
        trailingwesterndigits = list(str(trailingnumber))
    
        # Bail out if that didn't consume the whole input
        if trailingexpression.strip() != u"":
            return None
    
        if leadingnumber == 100:
            # Divisions out of 100 should be treated as percentages
            return percenthandler(trailingwesterndigits)
        else:
            # Otherwise treat as a straight fraction
            return fractionhandler(trailingwesterndigits, leadingwesterndigits)
    else:
        # Unknown suffix. We probably have to give up, but we MIGHT have had a year:
        leadingwesterndigits, trailingexpression = parsemany(parsehanzidigit)(expression)
        if trailingexpression == u"年":
            # Followed by a nian, return as a year
            return yearhandler(leadingwesterndigits)
        else:
            # Give up
            return None

def readingfromnumberlike(expression, dictionary):
    intify = lambda digits: int("".join(digits))
    
    # Here, we need to be careful to turn Western number-like things into readings
    # the way a Chinese person would say them
    return parsewesternnumberlike(expression,
            lambda digits: dictionary.reading(numberashanzi(intify(digits))),
            lambda leadingdigits, trailingdigits: dictionary.reading(numberashanzi(intify(leadingdigits)) + u"点" + "".join([numberashanzi(int(digit)) for digit in trailingdigits])),
            lambda digits: dictionary.reading("".join([numberashanzi(int(digit)) for digit in digits]) + u"年"),
            lambda digits: dictionary.reading(u"百分之" + numberashanzi(intify(digits))),
            lambda numdigits, denomdigits: dictionary.reading(numberashanzi(intify(denomdigits)) + u"分之" + numberashanzi(intify(numdigits))))

def meaningfromnumberlike(expression, dictionary):
    stringify = lambda digits: u"".join([unicode(digit) for digit in digits])
    handlers = [
        lambda digits: stringify(digits),
        lambda leadingdigits, trailingdigits: stringify(leadingdigits) + "." + stringify(trailingdigits),
        lambda digits: stringify(digits) + "AD",
        lambda digits: stringify(digits) + "%",
        lambda numdigits, denomdigits: stringify(numdigits) + "/" + stringify(denomdigits)
      ]
    
    # Generates a meaning from approximately Western expressions (almost useless, but does handle nian suffix)
    text = parsewesternnumberlike(expression, *handlers)
    
    if not(text):
        # Generate a meaning from approximately Chinese expressions
        text = parsechinesenumberlike(expression, *handlers)
        
    # Wrap the result in the appropriate gumpf
    return utils.bind_none(text, lambda nonnulltext: [[pinyin.Word(pinyin.Text(nonnulltext))]])

if __name__=='__main__':
    import unittest
    
    englishdict = utils.Thunk(lambda: dictionary.PinyinDictionary.load('en', True))
    
    class ReadingFromNumberlikeTest(unittest.TestCase):
        def testIntegerReading(self):
            self.assertReading("ba1 qian1 jiu3 bai3 er4 shi2 yi1", "8921")
        
        def testDecimalReading(self):
            self.assertReading("er4 shi2 wu3 dian3 er4 wu3", "25.25")
        
        def testYearReading(self):
            self.assertReading("yi1 jiu3 jiu3 ba1 nian2", u"1998年")
        
        def testPercentageReading(self):
            self.assertReading("bai3 fen1 zhi1 qi1 shi2", u"70%")
            self.assertReading("bai3 fen1 zhi1 qi1 shi2", u"70％")
        
        def testFractionReading(self):
            self.assertReading("san1 fen1 zhi1 yi1", "1/3")
            self.assertReading("san1 fen1 zhi1 yi1", "1\\3")
        
        def testNoReadingForPhrase(self):
            self.assertReading(None, u"你好")
        
        def testNoReadingForBlank(self):
            self.assertReading(None, u"")
            self.assertReading(None, u"24.")
            self.assertReading(None, u"24/")
        
        def testNoReadingsIfTrailingStuff(self):
            self.assertReading(None, u"8921A")
            self.assertReading(None, u"25.25A")
            self.assertReading(None, u"1998年A")
            self.assertReading(None, u"80%A")
            self.assertReading(None, u"80％A")
            self.assertReading(None, u"1/3A")
            self.assertReading(None, u"1\3A")
        
        # Test helpers
        def assertReading(self, expected_reading, expression):
            self.assertEquals(expected_reading, utils.bind_none(readingfromnumberlike(expression, englishdict), lambda reading: pinyin.flatten(reading)))
    
    class MeaningFromNumberlikeTest(unittest.TestCase):
        def testIntegerMeaning(self):
            self.assertMeaning("8921", "8921")
            self.assertMeaning("8921", u"八千九百二十一")
        
        def testDecimalMeaning(self):
            self.assertMeaning("25.25", "25.25")
            self.assertMeaning("25.25", u"25。25")
            self.assertMeaning("25.25", u"二十五点二五")
        
        def testYearMeaning(self):
            self.assertMeaning("1998AD", u"1998年")
            self.assertMeaning("1998AD", u"一九九八年")
        
        def testPercentageReading(self):
            self.assertMeaning("20%", u"百分之二十")
        
        def testFractionReading(self):
            self.assertMeaning("1/3", u"三分之一")
        
        def testNoMeaningForPhrase(self):
            self.assertMeaning(None, u"你好")
        
        def testNoMeaningForBlank(self):
            self.assertMeaning(None, u"")
            self.assertMeaning(None, u"24.")
        
        def testNoMeaningsIfTrailingStuff(self):
            self.assertMeaning(None, u"8921A")
            self.assertMeaning(None, u"八千九百二十一A")
            self.assertMeaning(None, u"25.25A")
            self.assertMeaning(None, u"25。25A")
            self.assertMeaning(None, u"二十五点二五A")
            self.assertMeaning(None, u"1998年A")
            self.assertMeaning(None, u"一九九八年A")
            self.assertMeaning(None, u"100%A")
            self.assertMeaning(None, u"百分之二十A")
            self.assertMeaning(None, u"1/3A")
            self.assertMeaning(None, u"1\3A")
            self.assertMeaning(None, u"三分之一A")
        
        # Test helpers
        def assertMeaning(self, expected_meaning, expression):
            self.assertEquals(expected_meaning, utils.bind_none(meaningfromnumberlike(expression, englishdict), lambda meanings: pinyin.flatten(meanings[0])))
    
    class NumberAsHanziTest(unittest.TestCase):
        def testSingleNumerals(self):
            self.assertEquals(numberashanzi(0), u"零")
            self.assertEquals(numberashanzi(5), u"五")
            self.assertEquals(numberashanzi(9), u"九")
        
        def testTooLargeNumber(self):
            self.assertEquals(numberashanzi(100000000000000000), u"100000000000000000")
        
        def testFullNumbers(self):
            self.assertEquals(numberashanzi(25), u"二十五")
            self.assertEquals(numberashanzi(8921), u"八千九百二十一")
        
        def testTruncationOfLowerUnits(self):
            self.assertEquals(numberashanzi(20), u"二十")
            self.assertEquals(numberashanzi(9000), u"九千")
            self.assertEquals(numberashanzi(9100), u"九千一百")

        def testSkippedOnes(self):
            self.assertEquals(numberashanzi(1), u"一")
            self.assertEquals(numberashanzi(10), u"十")
            self.assertEquals(numberashanzi(100), u"百")
            self.assertEquals(numberashanzi(1000), u"一千")

        def testSkippedMagnitudes(self):
            self.assertEquals(numberashanzi(9025), u"九千零二十五")
            self.assertEquals(numberashanzi(9020), u"九千零二十")
            self.assertEquals(numberashanzi(9005), u"九千零五")
    
    class HanziAsNumberTest(unittest.TestCase):
        def testSingleNumerals(self):
            self.assertHanziAsNumber(u"零", 0)
            self.assertHanziAsNumber(u"五", 5)
            self.assertHanziAsNumber(u"九", 9)
        
        def testLing(self):
            self.assertHanziAsNumber(u"零", 0)
            self.assertHanziAsNumber(u"零个", 0, expected_rest_hanzi=u"个")
        
        def testLiang(self):
            self.assertHanziAsNumber(u"两", 2)
            self.assertHanziAsNumber(u"两个", 2, expected_rest_hanzi=u"个")
        
        def testFullNumbers(self):
            self.assertHanziAsNumber(u"二十五", 25)
            self.assertHanziAsNumber(u"八千九百二十一", 8921)
        
        def testTruncationOfLowerUnits(self):
            self.assertHanziAsNumber(u"二十", 20)
            self.assertHanziAsNumber(u"九千", 9000)
            self.assertHanziAsNumber(u"九千一百", 9100)

        def testSkippedOnes(self):
            self.assertHanziAsNumber(u"一", 1)
            self.assertHanziAsNumber(u"十", 10)
            self.assertHanziAsNumber(u"百", 100)
            self.assertHanziAsNumber(u"一千", 1000)

        def testSkippedMagnitudes(self):
            self.assertHanziAsNumber(u"九千零二十五", 9025)
            self.assertHanziAsNumber(u"九千零二十", 9020)
            self.assertHanziAsNumber(u"九千零五", 9005)
        
        def testNonNumber(self):
            self.assertHanziAsNumber(u"一个", 1, expected_rest_hanzi=u"个")
            self.assertHanziAsNumber(u"个", None, expected_rest_hanzi=u"个")
    
        # Test helpers
        def assertHanziAsNumber(self, hanzi, expect_number, expected_rest_hanzi=""):
            actual_number, actual_rest_hanzi = parsehanziasnumber(hanzi)
            self.assertEquals(actual_rest_hanzi, expected_rest_hanzi)
            self.assertEquals(actual_number, expect_number)
    
    unittest.main()