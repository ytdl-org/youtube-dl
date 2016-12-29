#!/usr/bin/env python

"""
see: `jstests`
"""

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import copy
import logging

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.jsinterp.jsparser import Parser
from .jstests import gettestcases


def traverse(node, tree_types=(list, tuple)):
    if sys.version_info > (3,) and isinstance(node, zip):
        node = list(copy.copy(node))
    if isinstance(node, tree_types):
        tree = []
        for value in node:
            tree.append(traverse(value, tree_types))
        return tree
    else:
        return node


defs = gettestcases()
# set level to logging.DEBUG to see messages about not set ASTs
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)


class TestJSInterpreterParse(unittest.TestCase):
    def setUp(self):
        self.defs = defs


def generator(test_case, name):
    def test_template(self):
        for test in test_case['subtests']:
            if 'code' in test:
                jsp = Parser(test['code'])
                parsed = list(jsp.parse())
                if 'ast' in test:
                    self.assertEqual(traverse(parsed), traverse(test['ast']))
                else:
                    log.debug('No AST for subtest, trying to parse only')
            else:
                log.debug('No code in subtest, skipping')

    log = logging.getLogger('TestJSInterpreterParse.%s' % name)
    return test_template


# And add them to TestJSInterpreterParse
for n, tc in enumerate(defs):
    reason = tc['skip'].get('parse', False)
    tname = 'test_' + str(tc['name'])
    i = 1
    while hasattr(TestJSInterpreterParse, tname):
        tname = 'test_%s_%d' % (tc['name'], i)
        i += 1
    if reason is not True:
        test_method = generator(tc, tname)
        if reason is not False:
            test_method.__unittest_skip__ = True
            test_method.__unittest_skip_why__ = reason
        test_method.__name__ = str(tname)
        setattr(TestJSInterpreterParse, test_method.__name__, test_method)
        del test_method
    else:
        log = logging.getLogger('TestJSInterpreterParse')
        log.debug('Skipping %s:Entirely' % tname)


if __name__ == '__main__':
    unittest.main()
