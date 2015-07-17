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
    compat_urllib_parse_unquote,
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

    def test_compat_urllib_parse_unquote(self):
        test_strings = [
            ['''''', ''''''],
            ['''津波''', '''%E6%B4%A5%E6%B3%A2'''],
            ['''津波''', str('%E6%B4%A5%E6%B3%A2')],
            ['''<meta property="og:description" content="▁▂▃▄%▅▆▇█" />
%<a href="https://ar.wikipedia.org/wiki/تسونامي">%a''',
             '''<meta property="og:description" content="%E2%96%81%E2%96%82%E2%96%83%E2%96%84%25%E2%96%85%E2%96%86%E2%96%87%E2%96%88" />
%<a href="https://ar.wikipedia.org/wiki/%D8%AA%D8%B3%D9%88%D9%86%D8%A7%D9%85%D9%8A">%a'''],
            ['''(^◣_◢^)っ︻デ═一    ⇀    ⇀    ⇀    ⇀    ⇀    ↶%I%Break%Things%''',
             '''%28%5E%E2%97%A3_%E2%97%A2%5E%29%E3%81%A3%EF%B8%BB%E3%83%87%E2%95%90%E4%B8%80    %E2%87%80    %E2%87%80    %E2%87%80    %E2%87%80    %E2%87%80    %E2%86%B6%I%Break%25Things%''']
        ]
        for test in test_strings:
            strutf = test[0]
            strurlenc = test[1]
            strurldec = compat_urllib_parse_unquote(strurlenc)
            self.assertEqual(strutf, strurldec)
            self.assertEqual(strutf, compat_urllib_parse_unquote(strurlenc))

if __name__ == '__main__':
    unittest.main()
