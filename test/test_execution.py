#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

import unittest

import sys
import os
import subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.utils import encodeArgument
from youtube_dl.extractor import gen_extractors, get_info_extractor

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

ALL_EXTRACTORS = [ie.IE_NAME for ie in gen_extractors() if ie._WORKING]
EXTRACTOR_CASES = {
    'unrestricted': {
        'result': ALL_EXTRACTORS
    },
    'enable_all': {
        'enable': '*',
        'result': ALL_EXTRACTORS
    },
    'disable_all': {
        'disable': '*',
        'result': []
    },
    'enable_disable_all': {
        'enable': '*',
        'disable': '*',
        'result': []
    },
    'enable_some': {
        'enable': 'youtube,youporn',
        'result': ['youtube', 'YouPorn']
    },
    'enable_and_filter': {
        'enable': 'twitch:*',
        'disable': 'twitch:stream',
        'result': [ie for ie in ALL_EXTRACTORS if ie.startswith('twitch:') and ie != 'twitch:stream']
    },
    'enable_age_restricted': {
        'enable': 'youporn',
        'age_limit': 16,
        'result': []
    }
}

def gen_extractor_case(case):
    enable = case.get('enable')
    disable = case.get('disable')
    age_limit = case.get('age_limit')
    result = case['result']

    def template(self):
        args = [sys.executable, 'youtube_dl/__main__.py', '--list-extractors']
        if enable:
            args.extend(['--enable-extractors', enable])
        if disable:
            args.extend(['--disable-extractors', disable])
        if age_limit:
            args.extend(['--age-limit', str(age_limit)])

        out = subprocess.check_output(args, cwd=rootDir, stderr=_DEV_NULL).decode('utf-8')
        extractors = filter(lambda e: e and 'BROKEN' not in e, out.split('\n'))
        self.assertItemsEqual(extractors, result)

    return template

class TestExtractorSelection(unittest.TestCase):
    pass

for name, case in EXTRACTOR_CASES.items():
    test_method = gen_extractor_case(case)
    test_name = str('test_' + name)
    test_method.__name__ = test_name
    setattr(TestExtractorSelection, test_name, test_method)
    del test_method

if __name__ == '__main__':
    unittest.main()
