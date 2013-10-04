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

class TestDailymotionSubtitles(unittest.TestCase):
    def setUp(self):
        self.DL = FakeYDL()
        self.url = 'http://www.dailymotion.com/video/xczg00'
    def getInfoDict(self):
        IE = DailymotionIE(self.DL)
        info_dict = IE.extract(self.url)
        return info_dict
    def getSubtitles(self):
        info_dict = self.getInfoDict()
        return info_dict[0]['subtitles']
    def test_no_writesubtitles(self):
        subtitles = self.getSubtitles()
        self.assertEqual(subtitles, None)
    def test_subtitles(self):
        self.DL.params['writesubtitles'] = True
        subtitles = self.getSubtitles()
        self.assertEqual(md5(subtitles['en']), '976553874490cba125086bbfea3ff76f')
    def test_subtitles_lang(self):
        self.DL.params['writesubtitles'] = True
        self.DL.params['subtitleslangs'] = ['fr']
        subtitles = self.getSubtitles()
        self.assertEqual(md5(subtitles['fr']), '594564ec7d588942e384e920e5341792')
    def test_allsubtitles(self):
        self.DL.params['writesubtitles'] = True
        self.DL.params['allsubtitles'] = True
        subtitles = self.getSubtitles()
        self.assertEqual(len(subtitles.keys()), 5)
    def test_list_subtitles(self):
        self.DL.params['listsubtitles'] = True
        info_dict = self.getInfoDict()
        self.assertEqual(info_dict, None)
    def test_automatic_captions(self):
        self.DL.params['writeautomaticsub'] = True
        self.DL.params['subtitleslang'] = ['en']
        subtitles = self.getSubtitles()
        self.assertTrue(len(subtitles.keys()) == 0)
    def test_nosubtitles(self):
        self.url = 'http://www.dailymotion.com/video/x12u166_le-zapping-tele-star-du-08-aout-2013_tv'
        self.DL.params['writesubtitles'] = True
        self.DL.params['allsubtitles'] = True
        subtitles = self.getSubtitles()
        self.assertEqual(len(subtitles), 0)
    def test_multiple_langs(self):
        self.DL.params['writesubtitles'] = True
        langs = ['es', 'fr', 'de']
        self.DL.params['subtitleslangs'] = langs
        subtitles = self.getSubtitles()
        for lang in langs:
            self.assertTrue(subtitles.get(lang) is not None, u'Subtitles for \'%s\' not extracted' % lang)

if __name__ == '__main__':
    unittest.main()
