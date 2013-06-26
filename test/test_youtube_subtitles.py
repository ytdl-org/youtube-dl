#!/usr/bin/env python

import sys
import unittest
import json
import io
import hashlib

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.extractor import YoutubeIE
from youtube_dl.utils import *
from helper import FakeYDL

md5 = lambda s: hashlib.md5(s.encode('utf-8')).hexdigest()

class TestYoutubeSubtitles(unittest.TestCase):
    def setUp(self):
        DL = FakeYDL()
        DL.params['allsubtitles'] = False
        DL.params['writesubtitles'] = False
        DL.params['subtitlesformat'] = 'srt'
        DL.params['listsubtitles'] = False
    def test_youtube_no_subtitles(self):
        DL = FakeYDL()
        DL.params['writesubtitles'] = False
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        subtitles = info_dict[0]['subtitles']
        self.assertEqual(subtitles, None)
    def test_youtube_subtitles(self):
        DL = FakeYDL()
        DL.params['writesubtitles'] = True
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        sub = info_dict[0]['subtitles'][0]
        self.assertEqual(md5(sub[2]), '4cd9278a35ba2305f47354ee13472260')
    def test_youtube_subtitles_it(self):
        DL = FakeYDL()
        DL.params['writesubtitles'] = True
        DL.params['subtitleslang'] = 'it'
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        sub = info_dict[0]['subtitles'][0]
        self.assertEqual(md5(sub[2]), '164a51f16f260476a05b50fe4c2f161d')
    def test_youtube_onlysubtitles(self):
        DL = FakeYDL()
        DL.params['writesubtitles'] = True
        DL.params['onlysubtitles'] = True
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        sub = info_dict[0]['subtitles'][0]
        self.assertEqual(md5(sub[2]), '4cd9278a35ba2305f47354ee13472260')
    def test_youtube_allsubtitles(self):
        DL = FakeYDL()
        DL.params['allsubtitles'] = True
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        subtitles = info_dict[0]['subtitles']
        self.assertEqual(len(subtitles), 13)
    def test_youtube_subtitles_sbv_format(self):
        DL = FakeYDL()
        DL.params['writesubtitles'] = True
        DL.params['subtitlesformat'] = 'sbv'
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        sub = info_dict[0]['subtitles'][0]
        self.assertEqual(md5(sub[2]), '13aeaa0c245a8bed9a451cb643e3ad8b')
    def test_youtube_subtitles_vtt_format(self):
        DL = FakeYDL()
        DL.params['writesubtitles'] = True
        DL.params['subtitlesformat'] = 'vtt'
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        sub = info_dict[0]['subtitles'][0]
        self.assertEqual(md5(sub[2]), '356cdc577fde0c6783b9b822e7206ff7')
    def test_youtube_list_subtitles(self):
        DL = FakeYDL()
        DL.params['listsubtitles'] = True
        IE = YoutubeIE(DL)
        info_dict = IE.extract('QRS8MkLhQmM')
        self.assertEqual(info_dict, None)
    def test_youtube_automatic_captions(self):
        DL = FakeYDL()
        DL.params['writeautomaticsub'] = True
        DL.params['subtitleslang'] = 'it'
        IE = YoutubeIE(DL)
        info_dict = IE.extract('8YoUxe5ncPo')
        sub = info_dict[0]['subtitles'][0]
        self.assertTrue(sub[2] is not None)

if __name__ == '__main__':
    unittest.main()
