#!/usr/bin/env python
# -*- coding: utf-8 -*-

digits = [u"零", u"一", u"二", u"三", u"四", u"五", u"六", u"七", u"八", u"九"]

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


if __name__=='__main__':
    import unittest
    
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
    
    unittest.main()