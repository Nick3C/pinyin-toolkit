# -*- coding: utf-8 -*-

import nose.tools

assert_true = nose.tools.assert_true
assert_false = nose.tools.assert_false

assert_not_equal = nose.tools.assert_not_equal

def assert_equal(actual, expected):
    if type(expected) == dict:
        expect_dict_equal(actual, expected)
    else:
        nose.tools.assert_equal(actual, expected)

def assert_dict_equal(actual, expected, values_as_assertions=False):
    actualkeys = set(actual.keys())
    expectedkeys = set(expected.keys())
    nose.tools.assert_equal(actualkeys, expectedkeys, "\n".join(["Key sets differ", u"Only actual had: %s" % actualkeys.difference(expectedkeys), u"Only expected had: %s" % expectedkeys.difference(actualkeys)]))
    
    differences = []
    for key, expectedvalue in expected.items():
        actualvalue = actual[key]
        
        if values_as_assertions and hasattr(expectedvalue, "__call__"):
            expectedvalue(actualvalue)
        elif actualvalue != expectedvalue:
            differences.append((key, actualvalue, expectedvalue))
    
    if len(differences) > 0:
        raise AssertionError("\n".join(["Differences at:"] + [u"%r: %r != %r" % item for item in differences]))