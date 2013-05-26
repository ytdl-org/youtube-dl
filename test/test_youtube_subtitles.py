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
from youtube_dl import FileDownloader

PARAMETERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parameters.json")
with io.open(PARAMETERS_FILE, encoding='utf-8') as pf:
    parameters = json.load(pf)

# General configuration (from __init__, not very elegant...)
jar = compat_cookiejar.CookieJar()
cookie_processor = compat_urllib_request.HTTPCookieProcessor(jar)
proxy_handler = compat_urllib_request.ProxyHandler()
opener = compat_urllib_request.build_opener(proxy_handler, cookie_processor, YoutubeDLHandler())
compat_urllib_request.install_opener(opener)

class FakeDownloader(FileDownloader):
    def __init__(self):
        self.result = []
        # Different instances of the downloader can't share the same dictionary
        # some test set the "sublang" parameter, which would break the md5 checks.
        self.params = dict(parameters)
    def to_screen(self, s):
        print(s)
    def trouble(self, s, tb=None):
        raise Exception(s)
    def download(self, x):
        self.result.append(x)

md5 = lambda s: hashlib.md5(s.encode('utf-8')).hexdigest()

class TestYoutubeSubtitles(unittest.TestCase):
    def setUp(self):
        DL = FakeDownloader()
        DL.params['allsubtitles'] = False
        DL.params['writesubtitles'] = False
        DL.params['subtitlesformat'] = 'srt'
        DL.params['listsubtitles'] = False
    def test_youtube_no_subtitles(self):
        DL = FakeDownloader()
        DL.params['writesubtitles'] = False
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        subtitles = info_dict[0]['subtitles']
        self.assertEqual(subtitles, None)
    def test_youtube_subtitles(self):
        DL = FakeDownloader()
        DL.params['writesubtitles'] = True
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        sub = info_dict[0]['subtitles'][0]
        self.assertEqual(md5(sub[2]), '4cd9278a35ba2305f47354ee13472260')
    def test_youtube_subtitles_it(self):
        DL = FakeDownloader()
        DL.params['writesubtitles'] = True
        DL.params['subtitleslang'] = 'it'
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        sub = info_dict[0]['subtitles'][0]
        self.assertEqual(md5(sub[2]), '164a51f16f260476a05b50fe4c2f161d')
    def test_youtube_onlysubtitles(self):
        DL = FakeDownloader()
        DL.params['writesubtitles'] = True
        DL.params['onlysubtitles'] = True
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        sub = info_dict[0]['subtitles'][0]
        self.assertEqual(md5(sub[2]), '4cd9278a35ba2305f47354ee13472260')
    def test_youtube_allsubtitles(self):
        DL = FakeDownloader()
        DL.params['allsubtitles'] = True
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        subtitles = info_dict[0]['subtitles']
        self.assertEqual(len(subtitles), 13)
    def test_youtube_subtitles_format(self):
        DL = FakeDownloader()
        DL.params['writesubtitles'] = True
        DL.params['subtitlesformat'] = 'sbv'
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        sub = info_dict[0]['subtitles'][0]
        self.assertEqual(md5(sub[2]), '13aeaa0c245a8bed9a451cb643e3ad8b')
    def test_youtube_list_subtitles(self):
        DL = FakeDownloader()
        DL.params['listsubtitles'] = True
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        self.assertEqual(info_dict, None)
    def test_youtube_automatic_captions(self):
        DL = FakeDownloader()
        DL.params['writesubtitles'] = True
        DL.params['subtitleslang'] = 'it'
        IE = YoutubeIE(DL)
        info_dict = IE.extract('8YoUxe5ncPo')
        sub = info_dict[0]['subtitles'][0]
        self.assertTrue(sub[2] is not None)

if __name__ == '__main__':
    unittest.main()
