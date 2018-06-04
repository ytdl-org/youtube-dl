#!/usr/bin/env python

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import logging

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.jsinterp import JSInterpreter
from .js2tests import gettestcases

__doc__ = """see: `js2tests`"""


defs = gettestcases()
# set level to logging.DEBUG to see messages about missing assertions
# set level to logging.DEBUG to see messages about code tests are running
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger('TestJSInterpreter')


class TestJSInterpreter(unittest.TestCase):
    def setUp(self):
        self.defs = defs


def generator(test_case, my_log):
    def test_template(self):
        my_log.debug('Started...')
        for test in test_case['subtests']:
            excluded = test.get('exclude')
            if excluded is not None and 'jsinterp' in excluded:
                log_reason = 'jsinterp does not support this subtest:\n%s' % test['code']
            elif 'code' not in test:
                log_reason = 'No code in subtest, skipping'
            elif 'asserts' not in test:
                log_reason = 'No assertion in subtest, skipping'
            else:
                log_reason = None

            if log_reason is None:
                variables = test.get('globals')
                code = test['code']
                call = None

                if variables is not None:
                    code = 'function f(%s){%s}' % ((''.join(variables.keys())), code)
                    call = ('f',) + tuple(v for v in variables.values())
                    my_log.debug('globals: %s' % variables)
                my_log.debug(code)


                jsi = JSInterpreter(code, objects=variables)
                for assertion in test['asserts']:
                    if 'value' in assertion:
                        if call is None:
                            call = assertion['call']

                        if call is not None:
                            my_log.debug('call: %s(%s)' % (call[0], ', '.join(str(arg) for arg in call[1:])))

                        self.assertEqual(jsi.call_function(*call), assertion['value'])
                    else:
                        my_log.info('No value in assertion, skipping')
            else:
                my_log.info(log_reason)

    return test_template


# And add them to TestJSInterpreter
for testcase in defs:
    reason = testcase['skip'].get('jsinterp', False)
    tname = 'test_' + str(testcase['name'])
    i = 1
    while hasattr(TestJSInterpreter, tname):
        tname = 'test_%s_%d' % (testcase['name'], i)
        i += 1

    if reason is True:
        log_reason = 'Entirely'
    elif not any('asserts' in test for test in testcase['subtests']):
        log_reason = '''There isn't any assertion'''
    else:
        log_reason = None

    if log_reason is None:
        test_method = generator(testcase, log.getChild(tname))
        test_method.__name__ = str(tname)
        if reason is not False:
            test_method.__unittest_skip__ = True
            test_method.__unittest_skip_why__ = reason
        setattr(TestJSInterpreter, test_method.__name__, test_method)
        del test_method
    else:
        log.info('Skipping %s:%s' % (tname, log_reason))

if __name__ == '__main__':
    unittest.main()
