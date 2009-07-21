# -*- coding: utf-8 -*-

import unittest

from pinyin.statistics import *


class HanziDailyStatsTest(unittest.TestCase):
    def testNoDays(self):
        self.assertEquals(self.statsByDay([], 0), [])
    
    def testSingleDay(self):
        self.assertEquals(self.statsByDay([(u"的", 0)], 1), [
            (0, [1, 1, 0, 0, 0, 0])
          ])
    
    def testComplex(self):
        self.assertEquals(self.statsByDay([
            (u"的是斯", -1),
            (u"轴", 0),
            (u'暇TSHIRT', -3),
            (u'失斯', -1),
            (u'格捂Western Characters', -5),
            (u'', -3),
            (u'撞冒', -6),
            (u'迅迅迅迅迅', -10),
            (u'扛', -2)
          ], 5), [
            (-4, [5, 1, 3, 0, 0, 1]),
            (-3, [6, 1, 3, 0, 0, 2]),
            (-2, [7, 1, 4, 0, 0, 2]),
            (-1, [11, 3, 5, 1, 0, 2]),
            (0, [12, 3, 5, 1, 0, 3])
          ])
    
    def testZeroFirstAnsweredTreatedAsCreatedDate(self):
        self.assertEquals(self.stats([
            (u"的是斯", 0, self.nDaysAgo(-0)),
            (u"轴", self.nDaysAgo(0), self.nDaysAgo(30)),
            (u'暇', 0, self.nDaysAgo(-3))
          ], 2), [
            (-1, [1, 0, 0, 0, 0, 1]),
            (0, [5, 2, 0, 1, 0, 2])
          ])
    
    def testGetZeroesForDaysWithNoData(self):
        self.assertEquals(self.statsByDay([
            (u"的", -1),
          ], 3), [
            (-2, [0, 0, 0, 0, 0, 0]),
            (-1, [1, 1, 0, 0, 0, 0]),
            (0, [1, 1, 0, 0, 0, 0])
          ])
    
    def statsByDay(self, firstAnsweredValuesByDay, daysInRange):
        # Turn the day based time in the test into a seconds based one relative to the present
        # Zero out the created date because we will never need it
        firstAnsweredValues = [(value, self.nDaysAgo(firstAnsweredDay), 0) for value, firstAnsweredDay in firstAnsweredValuesByDay]
        return self.stats(firstAnsweredValues, daysInRange)
        
    def stats(self, firstAnsweredValues, daysInRange):
        # Actually do the test
        days, cumulativeTotals, cumulativesByGrades = hanziDailyStats(firstAnsweredValues, daysInRange)
        
        # Munge the result into a format more amenable to assertion: a list of (day, grade) pairs, where the grades
        # are presented in a list: total first, then by grade.
        return [(day, [cumulativeTotals[n]] + [cumulativesByGrades[grade][n] for grade in hanziGrades]) for n, day in enumerate(days)]
    
    def nDaysAgo(self, n):
        return (time.time() - 100) + (n * 86400.0)