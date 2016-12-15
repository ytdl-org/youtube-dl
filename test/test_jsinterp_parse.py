#!/usr/bin/env python

from __future__ import unicode_literals

import os
import sys
import copy

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.jsinterp import JSInterpreter
from test.jstests import gettestcases


def traverse(node, tree_types=(list, tuple)):
    if type(node) == zip:
        node = list(copy.deepcopy(node))
    if isinstance(node, tree_types):
        tree = []
        for value in node:
            tree.append(traverse(value, tree_types))
        return tree
    else:
        return node


defs = gettestcases()


class TestJSInterpreterParse(unittest.TestCase):
    def setUp(self):
        self.defs = defs


def generator(test_case):
    def test_template(self):
        for a in test_case['subtests']:
            jsi = JSInterpreter(a['code'], variables=None if 'globals' not in a else a['globals'])
            parsed = list(jsi.statements())
            if 'ast' in a:
                self.assertEqual(traverse(parsed), traverse(a['ast']))

    if 'p' not in test_case['skip']:
        reason = False
    else:
        reason = test_case['skip']['p']

    return test_template if not reason else unittest.skip(reason)(test_template)


# And add them to TestJSInterpreter
for n, tc in enumerate(defs):
    if 'p' not in tc['skip'] or tc['skip']['p'] is not True:
        test_method = generator(tc)
        tname = 'test_' + str(tc['name'])
        i = 1
        while hasattr(TestJSInterpreterParse, tname):
            tname = 'test_%s_%d' % (tc['name'], i)
            i += 1
        test_method.__name__ = str(tname)
        setattr(TestJSInterpreterParse, test_method.__name__, test_method)
        del test_method
