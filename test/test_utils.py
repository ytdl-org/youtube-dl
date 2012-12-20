#!/usr/bin/env python

# Various small unit tests

import sys
import unittest

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#from youtube_dl.utils import htmlentity_transform
from youtube_dl.utils import timeconvert
from youtube_dl.utils import sanitize_filename
from youtube_dl.utils import unescapeHTML
from youtube_dl.utils import orderedSet

if sys.version_info < (3, 0):
    _compat_str = lambda b: b.decode('unicode-escape')
else:
    _compat_str = lambda s: s


class TestUtil(unittest.TestCase):
    def test_timeconvert(self):
        self.assertTrue(timeconvert('') is None)
        self.assertTrue(timeconvert('bougrg') is None)

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename('abc'), 'abc')
        self.assertEqual(sanitize_filename('abc_d-e'), 'abc_d-e')

        self.assertEqual(sanitize_filename('123'), '123')

        self.assertEqual('abc_de', sanitize_filename('abc/de'))
        self.assertFalse('/' in sanitize_filename('abc/de///'))

        self.assertEqual('abc_de', sanitize_filename('abc/<>\\*|de'))
        self.assertEqual('xxx', sanitize_filename('xxx/<>\\*|'))
        self.assertEqual('yes no', sanitize_filename('yes? no'))
        self.assertEqual('this - that', sanitize_filename('this: that'))

        self.assertEqual(sanitize_filename('AT&T'), 'AT&T')
        aumlaut = _compat_str('\xe4')
        self.assertEqual(sanitize_filename(aumlaut), aumlaut)
        tests = _compat_str('\u043a\u0438\u0440\u0438\u043b\u043b\u0438\u0446\u0430')
        self.assertEqual(sanitize_filename(tests), tests)

        forbidden = '"\0\\/'
        for fc in forbidden:
            for fbc in forbidden:
                self.assertTrue(fbc not in sanitize_filename(fc))

    def test_sanitize_filename_restricted(self):
        self.assertEqual(sanitize_filename('abc', restricted=True), 'abc')
        self.assertEqual(sanitize_filename('abc_d-e', restricted=True), 'abc_d-e')

        self.assertEqual(sanitize_filename('123', restricted=True), '123')

        self.assertEqual('abc_de', sanitize_filename('abc/de', restricted=True))
        self.assertFalse('/' in sanitize_filename('abc/de///', restricted=True))

        self.assertEqual('abc_de', sanitize_filename('abc/<>\\*|de', restricted=True))
        self.assertEqual('xxx', sanitize_filename('xxx/<>\\*|', restricted=True))
        self.assertEqual('yes_no', sanitize_filename('yes? no', restricted=True))
        self.assertEqual('this_-_that', sanitize_filename('this: that', restricted=True))

        tests = _compat_str('a\xe4b\u4e2d\u56fd\u7684c')
        self.assertEqual(sanitize_filename(tests, restricted=True), 'a_b_c')
        self.assertTrue(sanitize_filename(_compat_str('\xf6'), restricted=True) != '')  # No empty filename

        forbidden = '"\0\\/&!: \'\t\n()[]{}$;`^,#'
        for fc in forbidden:
            for fbc in forbidden:
                self.assertTrue(fbc not in sanitize_filename(fc, restricted=True))

        # Handle a common case more neatly
        self.assertEqual(sanitize_filename(_compat_str('\u5927\u58f0\u5e26 - Song'), restricted=True), 'Song')
        self.assertEqual(sanitize_filename(_compat_str('\u603b\u7edf: Speech'), restricted=True), 'Speech')
        # .. but make sure the file name is never empty
        self.assertTrue(sanitize_filename('-', restricted=True) != '')
        self.assertTrue(sanitize_filename(':', restricted=True) != '')

    def test_sanitize_ids(self):
        self.assertEqual(sanitize_filename('_n_cd26wFpw', is_id=True), '_n_cd26wFpw')
        self.assertEqual(sanitize_filename('_BD_eEpuzXw', is_id=True), '_BD_eEpuzXw')
        self.assertEqual(sanitize_filename('N0Y__7-UOdI', is_id=True), 'N0Y__7-UOdI')

    def test_ordered_set(self):
        self.assertEqual(orderedSet([1, 1, 2, 3, 4, 4, 5, 6, 7, 3, 5]), [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(orderedSet([]), [])
        self.assertEqual(orderedSet([1]), [1])
        #keep the list ordered
        self.assertEqual(orderedSet([135, 1, 1, 1]), [135, 1])

    def test_unescape_html(self):
        self.assertEqual(unescapeHTML(_compat_str('%20;')), _compat_str('%20;'))

if __name__ == '__main__':
    unittest.main()
