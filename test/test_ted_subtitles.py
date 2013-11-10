#!/usr/bin/env python

import sys
import unittest
import hashlib

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.extractor import TEDIE
from youtube_dl.utils import *
from test.helper import FakeYDL, md5

class TestTedSubtitles(unittest.TestCase):
    def setUp(self):
        self.DL = FakeYDL()
        self.url = 'http://www.ted.com/talks/dan_dennett_on_our_consciousness.html'
    def getInfoDict(self):
        IE = TEDIE(self.DL)
        info_dict = IE.extract(self.url)
        return info_dict
    def getSubtitles(self):
        info_dict = self.getInfoDict()
        return info_dict['subtitles']
    def test_no_writesubtitles(self):
        subtitles = self.getSubtitles()
        self.assertEqual(subtitles, None)
    def test_subtitles(self):
        self.DL.params['writesubtitles'] = True
        subtitles = self.getSubtitles()
        self.assertEqual(md5(subtitles['en']), '2154f31ff9b9f89a0aa671537559c21d')
    def test_subtitles_lang(self):
        self.DL.params['writesubtitles'] = True
        self.DL.params['subtitleslangs'] = ['fr']
        subtitles = self.getSubtitles()
        self.assertEqual(md5(subtitles['fr']), '7616cbc6df20ec2c1204083c83871cf6')
    def test_allsubtitles(self):
        self.DL.params['writesubtitles'] = True
        self.DL.params['allsubtitles'] = True
        subtitles = self.getSubtitles()
        self.assertEqual(len(subtitles.keys()), 28)
    def test_list_subtitles(self):
        self.DL.params['listsubtitles'] = True
        info_dict = self.getInfoDict()
        self.assertEqual(info_dict, None)
    def test_automatic_captions(self):
        self.DL.params['writeautomaticsub'] = True
        self.DL.params['subtitleslang'] = ['en']
        subtitles = self.getSubtitles()
        self.assertTrue(len(subtitles.keys()) == 0)
    # def test_nosubtitles(self):
    #     self.DL.expect_warning(u'video doesn\'t have subtitles')
    #     self.url = 'http://www.ted.com/talks/rodrigo_canales_the_deadly_genius_of_drug_cartels.html'
    #     self.DL.params['writesubtitles'] = True
    #     self.DL.params['allsubtitles'] = True
    #     subtitles = self.getSubtitles()
    def test_multiple_langs(self):
        self.DL.params['writesubtitles'] = True
        langs = ['es', 'fr', 'de']
        self.DL.params['subtitleslangs'] = langs
        subtitles = self.getSubtitles()
        for lang in langs:
            self.assertTrue(subtitles.get(lang) is not None, u'Subtitles for \'%s\' not extracted' % lang)

if __name__ == '__main__':
    unittest.main()
