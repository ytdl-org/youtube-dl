#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

import unittest

import sys
import os
import subprocess

rootDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, rootDir)

from youtube_dl.compat import compat_register_utf8, compat_subprocess_get_DEVNULL
from youtube_dl.utils import encodeArgument

compat_register_utf8()


_DEV_NULL = compat_subprocess_get_DEVNULL()


class TestExecution(unittest.TestCase):
    def setUp(self):
        self.module = 'youtube_dl'
        if sys.version_info < (2, 7):
            self.module += '.__main__'

    def test_import(self):
        subprocess.check_call([sys.executable, '-c', 'import youtube_dl'], cwd=rootDir)

    def test_module_exec(self):
        subprocess.check_call([sys.executable, '-m', self.module, '--version'], cwd=rootDir, stdout=_DEV_NULL)

    def test_main_exec(self):
        subprocess.check_call([sys.executable, os.path.normpath('youtube_dl/__main__.py'), '--version'], cwd=rootDir, stdout=_DEV_NULL)

    def test_cmdline_umlauts(self):
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        p = subprocess.Popen(
            [sys.executable, '-m', self.module, encodeArgument('ä'), '--version'],
            cwd=rootDir, stdout=_DEV_NULL, stderr=subprocess.PIPE)
        _, stderr = p.communicate()
        self.assertFalse(stderr)

    def test_lazy_extractors(self):
        lazy_extractors = os.path.normpath('youtube_dl/extractor/lazy_extractors.py')
        try:
            subprocess.check_call([sys.executable, os.path.normpath('devscripts/make_lazy_extractors.py'), lazy_extractors], cwd=rootDir, stdout=_DEV_NULL)
            subprocess.check_call([sys.executable, os.path.normpath('test/test_all_urls.py')], cwd=rootDir, stdout=_DEV_NULL)
        finally:
            for x in ('', 'c') if sys.version_info[0] < 3 else ('',):
                try:
                    os.remove(lazy_extractors + x)
                except OSError:
                    pass


if __name__ == '__main__':
    unittest.main()
