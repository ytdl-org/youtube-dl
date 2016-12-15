#!/usr/bin/env python

from __future__ import unicode_literals

import os
import sys
import logging

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.jsinterp import JSInterpreter
from test.jstests import gettestcases

defs = gettestcases()
# set level to logging.DEBUG to see messages about missing assertions
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)


class TestJSInterpreter(unittest.TestCase):
    def setUp(self):
        self.defs = defs


def generator(test_case, name):
    def test_template(self):
        for test in test_case['subtests']:
            jsi = JSInterpreter(test['code'], variables=None if 'globals' not in test else test['globals'])
            if 'asserts' in test:
                for a in test['asserts']:
                    if 'call' in a:
                        self.assertEqual(jsi.call_function(*a['call']), a['value'])
                    else:
                        self.assertEqual(jsi.run(), a['value'])
            else:
                log.debug('No asserts, skipping subtest')

    log = logging.getLogger('TestJSInterpreter.%s' % name)

    if 'i' not in test_case['skip']:
        reason = False
    else:
        reason = test_case['skip']['i']

    return test_template if not reason else unittest.skip(reason)(test_template)


# And add them to TestJSInterpreter
for n, tc in enumerate(defs):
    if 'i' not in tc['skip'] or tc['skip']['i'] is not True:
        tname = 'test_' + str(tc['name'])
        i = 1
        while hasattr(TestJSInterpreter, tname):
            tname = 'test_%s_%d' % (tc['name'], i)
            i += 1
        if any('asserts' in test for test in tc['subtests']):
            test_method = generator(tc, tname)
            test_method.__name__ = str(tname)
            setattr(TestJSInterpreter, test_method.__name__, test_method)
            del test_method
        else:
            log = logging.getLogger('TestJSInterpreter')
            log.debug('''Skipping %s:There isn't any assertion''' % tname)

if __name__ == '__main__':
    unittest.main()
