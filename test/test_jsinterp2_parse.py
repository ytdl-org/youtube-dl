#!/usr/bin/env python

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

from youtube_dl.jsinterp2.jsparser import Parser
from .js2tests import gettestcases

__doc__ = """see: `js2tests`"""


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
# set level to logging.INFO to see messages about not set ASTs
# set level to logging.DEBUG to see messages about code tests are running
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
log = logging.getLogger('TestJSInterpreter2Parse')


class TestJSInterpreter2Parse(unittest.TestCase):
    def setUp(self):
        self.defs = defs


def generator(test_case, my_log):
    def test_template(self):
        my_log.debug('Started...')
        for test in test_case['subtests']:
            if 'code' in test:
                code = test['code']
                my_log.debug(code)

                jsp = Parser(code)
                parsed = list(jsp.parse())
                if 'ast' in test:
                    self.assertEqual(traverse(parsed), traverse(test['ast']))
                else:
                    my_log.info('No AST for subtest, trying to parse only')
            else:
                my_log.info('No code in subtest, skipping')

    return test_template


# And add them to TestJSInterpreter2Parse
for testcase in defs:
    reason = testcase['skip'].get('parse', False)
    tname = 'test_' + str(testcase['name'])
    i = 1
    while hasattr(TestJSInterpreter2Parse, tname):
        tname = 'test_%s_%d' % (testcase['name'], i)
        i += 1

    if reason is True:
        log_reason = 'Entirely'
    elif not any('asserts' in test for test in testcase['subtests']):
        log_reason = '''There isn't any assertion'''
    else:
        log_reason = None

    if log_reason is None:
        test_method = generator(testcase, logging.getLogger('.'.join((log.name, tname))))
        test_method.__name__ = str(tname)
        if reason is not False:
            test_method.__unittest_skip__ = True
            test_method.__unittest_skip_why__ = reason
        setattr(TestJSInterpreter2Parse, test_method.__name__, test_method)
        del test_method
    else:
        log.info('Skipping %s:%s' % (tname, log_reason))


if __name__ == '__main__':
    unittest.main()
