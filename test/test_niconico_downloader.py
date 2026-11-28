#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals

import subprocess
import sys
import unittest


class TestNiconicoDownloader(unittest.TestCase):
    def test_no_syntax_warning_return_in_finally(self):
        """Issue #33243: 'return' in a 'finally' block triggers SyntaxWarning in Python 3.14+"""
        result = subprocess.run(
            [sys.executable, '-W', 'error::SyntaxWarning', '-c',
             'from youtube_dl.downloader.niconico import NiconicoDmcFD'],
            capture_output=True, text=True)
        self.assertEqual(
            result.returncode, 0,
            'Importing niconico downloader raised SyntaxWarning '
            '(return in finally block):\n' + result.stderr)


if __name__ == '__main__':
    unittest.main()
