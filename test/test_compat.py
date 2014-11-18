#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from youtube_dl.utils import get_filesystem_encoding
from youtube_dl.compat import (
    compat_getenv,
    compat_expanduser,
)


class TestCompat(unittest.TestCase):
    def test_compat_getenv(self):
        test_str = 'тест'
        os.environ['YOUTUBE-DL-TEST'] = (
            test_str if sys.version_info >= (3, 0)
            else test_str.encode(get_filesystem_encoding()))
        self.assertEqual(compat_getenv('YOUTUBE-DL-TEST'), test_str)

    def test_compat_expanduser(self):
        old_home = os.environ.get('HOME')
        test_str = 'C:\Documents and Settings\тест\Application Data'
        os.environ['HOME'] = (
            test_str if sys.version_info >= (3, 0)
            else test_str.encode(get_filesystem_encoding()))
        self.assertEqual(compat_expanduser('~'), test_str)
        os.environ['HOME'] = old_home

    def test_all_present(self):
        import youtube_dl.compat
        all_names = youtube_dl.compat.__all__
        present_names = set(filter(
            lambda c: '_' in c and not c.startswith('_'),
            dir(youtube_dl.compat))) - set(['unicode_literals'])
        self.assertEqual(all_names, sorted(present_names))

if __name__ == '__main__':
    unittest.main()
