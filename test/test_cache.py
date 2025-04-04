#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shutil

from test.helper import FakeYDL
from youtube_dl.cache import Cache
from youtube_dl.utils import version_tuple
from youtube_dl.version import __version__


def _is_empty(d):
    return not bool(os.listdir(d))


def _mkdir(d):
    if not os.path.exists(d):
        os.mkdir(d)


class TestCache(unittest.TestCase):
    def setUp(self):
        TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        TESTDATA_DIR = os.path.join(TEST_DIR, 'testdata')
        _mkdir(TESTDATA_DIR)
        self.test_dir = os.path.join(TESTDATA_DIR, 'cache_test')
        self.tearDown()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_cache(self):
        ydl = FakeYDL({
            'cachedir': self.test_dir,
        })
        c = Cache(ydl)
        obj = {'x': 1, 'y': ['ä', '\\a', True]}
        self.assertEqual(c.load('test_cache', 'k.'), None)
        c.store('test_cache', 'k.', obj)
        self.assertEqual(c.load('test_cache', 'k2'), None)
        self.assertFalse(_is_empty(self.test_dir))
        self.assertEqual(c.load('test_cache', 'k.'), obj)
        self.assertEqual(c.load('test_cache', 'y'), None)
        self.assertEqual(c.load('test_cache2', 'k.'), None)
        c.remove()
        self.assertFalse(os.path.exists(self.test_dir))
        self.assertEqual(c.load('test_cache', 'k.'), None)

    def test_cache_validation(self):
        ydl = FakeYDL({
            'cachedir': self.test_dir,
        })
        c = Cache(ydl)
        obj = {'x': 1, 'y': ['ä', '\\a', True]}
        c.store('test_cache', 'k.', obj)
        self.assertEqual(c.load('test_cache', 'k.', min_ver='1970.01.01'), obj)
        new_version = '.'.join(('%0.2d' % ((v + 1) if i == 0 else v, )) for i, v in enumerate(version_tuple(__version__)))
        self.assertIs(c.load('test_cache', 'k.', min_ver=new_version), None)


if __name__ == '__main__':
    unittest.main()
