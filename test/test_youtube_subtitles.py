#!/usr/bin/env python

import sys
import unittest
import json
import io
import hashlib

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.InfoExtractors import YoutubeIE
from youtube_dl.utils import *

PARAMETERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parameters.json")
with io.open(PARAMETERS_FILE, encoding='utf-8') as pf:
    parameters = json.load(pf)

# General configuration (from __init__, not very elegant...)
jar = compat_cookiejar.CookieJar()
cookie_processor = compat_urllib_request.HTTPCookieProcessor(jar)
proxy_handler = compat_urllib_request.ProxyHandler()
opener = compat_urllib_request.build_opener(proxy_handler, cookie_processor, YoutubeDLHandler())
compat_urllib_request.install_opener(opener)

class FakeDownloader(object):
    def __init__(self):
        self.result = []
        self.params = parameters
    def to_screen(self, s):
        print(s)
    def trouble(self, s):
        raise Exception(s)
    def download(self, x):
        self.result.append(x)

md5 = lambda s: hashlib.md5(s.encode('utf-8')).hexdigest()

class TestYoutubeSubtitles(unittest.TestCase):
    def test_youtube_subtitles(self):
        DL = FakeDownloader()
        DL.params['writesubtitles'] = True
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        self.assertEqual(md5(info_dict[0]['subtitles']), 'c3228550d59116f3c29fba370b55d033')

    def test_youtube_subtitles_it(self):
        DL = FakeDownloader()
        DL.params['writesubtitles'] = True
        DL.params['subtitleslang'] = 'it'
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        self.assertEqual(md5(info_dict[0]['subtitles']), '132a88a0daf8e1520f393eb58f1f646a')

if __name__ == '__main__':
    unittest.main()
