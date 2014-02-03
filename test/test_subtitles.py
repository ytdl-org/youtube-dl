#!/usr/bin/env python

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL, md5


from youtube_dl.extractor import (
    BlipTVIE,
    YoutubeIE,
    DailymotionIE,
    TEDIE,
    VimeoIE,
)


class BaseTestSubtitles(unittest.TestCase):
    url = None
    IE = None
    def setUp(self):
        self.DL = FakeYDL()
        self.ie = self.IE(self.DL)

    def getInfoDict(self):
        info_dict = self.ie.extract(self.url)
        return info_dict

    def getSubtitles(self):
        info_dict = self.getInfoDict()
        return info_dict['subtitles']


class TestYoutubeSubtitles(BaseTestSubtitles):
    url = 'QRS8MkLhQmM'
    IE = YoutubeIE

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
        self.assertEqual(md5(subtitles['en']), '3cb210999d3e021bd6c7f0ea751eab06')

    def test_youtube_list_subtitles(self):
        self.DL.expect_warning(u'Video doesn\'t have automatic captions')
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
        self.DL.expect_warning(u'video doesn\'t have subtitles')
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


class TestDailymotionSubtitles(BaseTestSubtitles):
    url = 'http://www.dailymotion.com/video/xczg00'
    IE = DailymotionIE

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
        self.DL.expect_warning(u'Automatic Captions not supported by this server')
        self.DL.params['listsubtitles'] = True
        info_dict = self.getInfoDict()
        self.assertEqual(info_dict, None)

    def test_automatic_captions(self):
        self.DL.expect_warning(u'Automatic Captions not supported by this server')
        self.DL.params['writeautomaticsub'] = True
        self.DL.params['subtitleslang'] = ['en']
        subtitles = self.getSubtitles()
        self.assertTrue(len(subtitles.keys()) == 0)

    def test_nosubtitles(self):
        self.DL.expect_warning(u'video doesn\'t have subtitles')
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


class TestTedSubtitles(BaseTestSubtitles):
    url = 'http://www.ted.com/talks/dan_dennett_on_our_consciousness.html'
    IE = TEDIE

    def test_no_writesubtitles(self):
        subtitles = self.getSubtitles()
        self.assertEqual(subtitles, None)

    def test_subtitles(self):
        self.DL.params['writesubtitles'] = True
        subtitles = self.getSubtitles()
        self.assertEqual(md5(subtitles['en']), '4262c1665ff928a2dada178f62cb8d14')

    def test_subtitles_lang(self):
        self.DL.params['writesubtitles'] = True
        self.DL.params['subtitleslangs'] = ['fr']
        subtitles = self.getSubtitles()
        self.assertEqual(md5(subtitles['fr']), '66a63f7f42c97a50f8c0e90bc7797bb5')

    def test_allsubtitles(self):
        self.DL.params['writesubtitles'] = True
        self.DL.params['allsubtitles'] = True
        subtitles = self.getSubtitles()
        self.assertEqual(len(subtitles.keys()), 28)

    def test_list_subtitles(self):
        self.DL.expect_warning(u'Automatic Captions not supported by this server')
        self.DL.params['listsubtitles'] = True
        info_dict = self.getInfoDict()
        self.assertEqual(info_dict, None)

    def test_automatic_captions(self):
        self.DL.expect_warning(u'Automatic Captions not supported by this server')
        self.DL.params['writeautomaticsub'] = True
        self.DL.params['subtitleslang'] = ['en']
        subtitles = self.getSubtitles()
        self.assertTrue(len(subtitles.keys()) == 0)

    def test_multiple_langs(self):
        self.DL.params['writesubtitles'] = True
        langs = ['es', 'fr', 'de']
        self.DL.params['subtitleslangs'] = langs
        subtitles = self.getSubtitles()
        for lang in langs:
            self.assertTrue(subtitles.get(lang) is not None, u'Subtitles for \'%s\' not extracted' % lang)


class TestBlipTVSubtitles(BaseTestSubtitles):
    url = 'http://blip.tv/a/a-6603250'
    IE = BlipTVIE

    def test_list_subtitles(self):
        self.DL.expect_warning(u'Automatic Captions not supported by this server')
        self.DL.params['listsubtitles'] = True
        info_dict = self.getInfoDict()
        self.assertEqual(info_dict, None)

    def test_allsubtitles(self):
        self.DL.expect_warning(u'Automatic Captions not supported by this server')
        self.DL.params['writesubtitles'] = True
        self.DL.params['allsubtitles'] = True
        subtitles = self.getSubtitles()
        self.assertEqual(set(subtitles.keys()), set(['en']))
        self.assertEqual(md5(subtitles['en']), '5b75c300af65fe4476dff79478bb93e4')


class TestVimeoSubtitles(BaseTestSubtitles):
    url = 'http://vimeo.com/76979871'
    IE = VimeoIE

    def test_no_writesubtitles(self):
        subtitles = self.getSubtitles()
        self.assertEqual(subtitles, None)

    def test_subtitles(self):
        self.DL.params['writesubtitles'] = True
        subtitles = self.getSubtitles()
        self.assertEqual(md5(subtitles['en']), '8062383cf4dec168fc40a088aa6d5888')

    def test_subtitles_lang(self):
        self.DL.params['writesubtitles'] = True
        self.DL.params['subtitleslangs'] = ['fr']
        subtitles = self.getSubtitles()
        self.assertEqual(md5(subtitles['fr']), 'b6191146a6c5d3a452244d853fde6dc8')

    def test_allsubtitles(self):
        self.DL.params['writesubtitles'] = True
        self.DL.params['allsubtitles'] = True
        subtitles = self.getSubtitles()
        self.assertEqual(set(subtitles.keys()), set(['de', 'en', 'es', 'fr']))

    def test_list_subtitles(self):
        self.DL.expect_warning(u'Automatic Captions not supported by this server')
        self.DL.params['listsubtitles'] = True
        info_dict = self.getInfoDict()
        self.assertEqual(info_dict, None)

    def test_automatic_captions(self):
        self.DL.expect_warning(u'Automatic Captions not supported by this server')
        self.DL.params['writeautomaticsub'] = True
        self.DL.params['subtitleslang'] = ['en']
        subtitles = self.getSubtitles()
        self.assertTrue(len(subtitles.keys()) == 0)

    def test_nosubtitles(self):
        self.DL.expect_warning(u'video doesn\'t have subtitles')
        self.url = 'http://vimeo.com/56015672'
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
