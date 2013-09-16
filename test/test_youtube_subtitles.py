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
        self.DL = FakeYDL()
        self.url = 'QRS8MkLhQmM'
    def getInfoDict(self):
        IE = YoutubeIE(self.DL)
        info_dict = IE.extract(self.url)
        return info_dict
    def getSubtitles(self):
        info_dict = self.getInfoDict()
        return info_dict[0]['subtitles']        
    def test_youtube_no_writesubtitles(self):
        self.DL.params['writesubtitles'] = False
        subtitles = self.getSubtitles()
        self.assertEqual(subtitles, None)
    def test_youtube_subtitles(self):
        self.DL.params['writesubtitles'] = True
        subtitles = self.getSubtitles()
        self.assertEqual(md5(subtitles['en']), '4cd9278a35ba2305f47354ee13472260')
    def test_youtube_subtitles_lang(self):
        self.DL.params['writesubtitles'] = True
        self.DL.params['subtitleslangs'] = ['it']
        subtitles = self.getSubtitles()
        self.assertEqual(md5(subtitles['it']), '164a51f16f260476a05b50fe4c2f161d')
    def test_youtube_allsubtitles(self):
        self.DL.params['writesubtitles'] = True
        self.DL.params['allsubtitles'] = True
        subtitles = self.getSubtitles()
        self.assertEqual(len(subtitles.keys()), 13)
    def test_youtube_subtitles_sbv_format(self):
        self.DL.params['writesubtitles'] = True
        self.DL.params['subtitlesformat'] = 'sbv'
        subtitles = self.getSubtitles()
        self.assertEqual(md5(subtitles['en']), '13aeaa0c245a8bed9a451cb643e3ad8b')
    def test_youtube_subtitles_vtt_format(self):
        self.DL.params['writesubtitles'] = True
        self.DL.params['subtitlesformat'] = 'vtt'
        subtitles = self.getSubtitles()
        self.assertEqual(md5(subtitles['en']), '356cdc577fde0c6783b9b822e7206ff7')
    def test_youtube_list_subtitles(self):
        self.DL.params['listsubtitles'] = True
        info_dict = self.getInfoDict()
        self.assertEqual(info_dict, None)
    def test_youtube_automatic_captions(self):
        self.url = '8YoUxe5ncPo'
        self.DL.params['writeautomaticsub'] = True
        self.DL.params['subtitleslangs'] = ['it']
        subtitles = self.getSubtitles()
        self.assertTrue(subtitles['it'] is not None)
    def test_youtube_nosubtitles(self):
        self.url = 'sAjKT8FhjI8'
        self.DL.params['writesubtitles'] = True
        self.DL.params['allsubtitles'] = True
        subtitles = self.getSubtitles()
        self.assertEqual(len(subtitles), 0)
    def test_youtube_multiple_langs(self):
        self.url = 'QRS8MkLhQmM'
        self.DL.params['writesubtitles'] = True
        langs = ['it', 'fr', 'de']
        self.DL.params['subtitleslangs'] = langs
        subtitles = self.getSubtitles()
        for lang in langs:
            self.assertTrue(subtitles.get(lang) is not None, u'Subtitles for \'%s\' not extracted' % lang)

if __name__ == '__main__':
    unittest.main()
