#!/usr/bin/env python

import sys
import unittest
import json
import io
import hashlib

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.extractor import DailymotionIE
from youtube_dl.utils import *
from helper import FakeYDL

md5 = lambda s: hashlib.md5(s.encode('utf-8')).hexdigest()
TEST_URL = 'http://www.dailymotion.com/video/xczg00'

class TestDailymotionSubtitles(unittest.TestCase):
    def setUp(self):
        DL = FakeYDL()
        DL.params['allsubtitles'] = False
        DL.params['writesubtitles'] = False
        DL.params['subtitlesformat'] = 'srt'
        DL.params['listsubtitles'] = False
    def test_no_subtitles(self):
        DL = FakeYDL()
        DL.params['writesubtitles'] = False
        IE = DailymotionIE(DL)
        info_dict = IE.extract(TEST_URL)
        subtitles = info_dict[0]['subtitles']
        self.assertEqual(subtitles, None)
    def test_subtitles(self):
        DL = FakeYDL()
        DL.params['writesubtitles'] = True
        IE = DailymotionIE(DL)
        info_dict = IE.extract(TEST_URL)
        sub = info_dict[0]['subtitles']['en']
        self.assertEqual(md5(sub), '976553874490cba125086bbfea3ff76f')
    def test_subtitles_fr(self):
        DL = FakeYDL()
        DL.params['writesubtitles'] = True
        DL.params['subtitleslang'] = 'fr'
        IE = DailymotionIE(DL)
        info_dict = IE.extract(TEST_URL)
        sub = info_dict[0]['subtitles']['fr']
        self.assertEqual(md5(sub), '594564ec7d588942e384e920e5341792')
    def test_onlysubtitles(self):
        DL = FakeYDL()
        DL.params['writesubtitles'] = True
        DL.params['onlysubtitles'] = True
        IE = DailymotionIE(DL)
        info_dict = IE.extract(TEST_URL)
        sub = info_dict[0]['subtitles']['en']
        self.assertEqual(md5(sub), '976553874490cba125086bbfea3ff76f')
    def test_allsubtitles(self):
        DL = FakeYDL()
        DL.params['allsubtitles'] = True
        IE = DailymotionIE(DL)
        info_dict = IE.extract(TEST_URL)
        subtitles = info_dict[0]['subtitles']
        self.assertEqual(len(subtitles.keys()), 5)
    # def test_subtitles_sbv_format(self):
    #     DL = FakeYDL()
    #     DL.params['writesubtitles'] = True
    #     DL.params['subtitlesformat'] = 'sbv'
    #     IE = DailymotionIE(DL)
    #     info_dict = IE.extract(TEST_URL)
    #     sub = info_dict[0]['subtitles'][0]
    #     self.assertEqual(md5(sub), '13aeaa0c245a8bed9a451cb643e3ad8b')
    # def test_subtitles_vtt_format(self):
    #     DL = FakeYDL()
    #     DL.params['writesubtitles'] = True
    #     DL.params['subtitlesformat'] = 'vtt'
    #     IE = DailymotionIE(DL)
    #     info_dict = IE.extract(TEST_URL)
    #     sub = info_dict[0]['subtitles'][0]
    #     self.assertEqual(md5(sub), '356cdc577fde0c6783b9b822e7206ff7')
    def test_list_subtitles(self):
        DL = FakeYDL()
        DL.params['listsubtitles'] = True
        IE = DailymotionIE(DL)
        info_dict = IE.extract(TEST_URL)
        self.assertEqual(info_dict, None)
    def test_automatic_captions(self):
        DL = FakeYDL()
        DL.params['writeautomaticsub'] = True
        DL.params['subtitleslang'] = 'en'
        IE = DailymotionIE(DL)
        info_dict = IE.extract(TEST_URL)
        sub = info_dict[0]['subtitles']
        self.assertTrue(len(sub) == 0)

if __name__ == '__main__':
    unittest.main()
