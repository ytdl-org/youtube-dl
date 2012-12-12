#!/usr/bin/env python

import hashlib
import io
import os
import json
import unittest
import sys
import socket

# Allow direct execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import youtube_dl.FileDownloader
import youtube_dl.InfoExtractors
from youtube_dl.utils import *

DEF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests.json')
PARAMETERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parameters.json")

# General configuration (from __init__, not very elegant...)
jar = compat_cookiejar.CookieJar()
cookie_processor = compat_urllib_request.HTTPCookieProcessor(jar)
proxy_handler = compat_urllib_request.ProxyHandler()
opener = compat_urllib_request.build_opener(proxy_handler, cookie_processor, YoutubeDLHandler())
compat_urllib_request.install_opener(opener)
socket.setdefaulttimeout(300) # 5 minutes should be enough (famous last words)

class FileDownloader(youtube_dl.FileDownloader):
    def __init__(self, *args, **kwargs):
        youtube_dl.FileDownloader.__init__(self, *args, **kwargs)
        self.to_stderr = self.to_screen

def _file_md5(fn):
    with open(fn, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

with io.open(DEF_FILE, encoding='utf-8') as deff:
    defs = json.load(deff)
with io.open(PARAMETERS_FILE, encoding='utf-8') as pf:
    parameters = json.load(pf)

class TestDownload(unittest.TestCase):
    def setUp(self):
        self.parameters = parameters
        self.defs = defs

        # Clear old files
        self.tearDown()

    def tearDown(self):
        for test in self.defs:
            fn = test['file']
            if fn and os.path.exists(fn):
                os.remove(fn)


def make_test_method(test_case):
    def test_template(self):
        ie = getattr(youtube_dl.InfoExtractors, test_case['name'] + 'IE')
        if not ie._WORKING:
            print('Skipping: IE marked as not _WORKING')
            return
        if not test_case['file']:
            print('Skipping: No output file specified')
            return
        if 'skip' in test_case:
            print('Skipping: {0}'.format(test_case['skip']))
            return
        params = dict(self.parameters) # Duplicate it locally
        for p in test_case.get('params', {}):
            params[p] = test_case['params'][p]
        fd = FileDownloader(params)
        fd.add_info_extractor(ie())
        for ien in test_case.get('add_ie', []):
            fd.add_info_extractor(getattr(youtube_dl.InfoExtractors, ien + 'IE')())
        fd.download([test_case['url']])
        self.assertTrue(os.path.exists(test_case['file']))
        if 'md5' in test_case:
            md5_for_file = _file_md5(test_case['file'])
            self.assertEqual(md5_for_file, test_case['md5'])

    # TODO proper skipping annotations
    return test_template

for test_case in defs:
    test_method = make_test_method(test_case)
    test_method.__name__ = "test_{0}".format(test_case["name"])
    setattr(TestDownload, test_method.__name__, test_method)


if __name__ == '__main__':
    unittest.main()
