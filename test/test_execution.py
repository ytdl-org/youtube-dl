#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

import unittest

import sys
import os
import subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.utils import encodeArgument

rootDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


try:
    _DEV_NULL = subprocess.DEVNULL
except AttributeError:
    _DEV_NULL = open(os.devnull, 'wb')


class TestExecution(unittest.TestCase):
    def test_import(self):
        subprocess.check_call([sys.executable, '-c', 'import youtube_dl'], cwd=rootDir)

    def test_module_exec(self):
        if sys.version_info >= (2, 7):  # Python 2.6 doesn't support package execution
            subprocess.check_call([sys.executable, '-m', 'youtube_dl', '--version'], cwd=rootDir, stdout=_DEV_NULL)

    def test_main_exec(self):
        subprocess.check_call([sys.executable, 'youtube_dl/__main__.py', '--version'], cwd=rootDir, stdout=_DEV_NULL)

    def test_cmdline_umlauts(self):
        p = subprocess.Popen(
            [sys.executable, 'youtube_dl/__main__.py', encodeArgument('ä'), '--version'],
            cwd=rootDir, stdout=_DEV_NULL, stderr=subprocess.PIPE)
        _, stderr = p.communicate()
        self.assertFalse(stderr)

    def test_lazy_extractors(self):
        lazy_extractors = 'youtube_dl/extractor/lazy_extractors.py'
        try:
            subprocess.check_call([sys.executable, 'devscripts/make_lazy_extractors.py', lazy_extractors], cwd=rootDir, stdout=_DEV_NULL)
            subprocess.check_call([sys.executable, 'test/test_all_urls.py'], cwd=rootDir, stdout=_DEV_NULL)
        finally:
            for x in ['', 'c'] if sys.version_info[0] < 3 else ['']:
                try:
                    os.remove(lazy_extractors + x)
                except (IOError, OSError):
                    pass


if __name__ == '__main__':
    unittest.main()
