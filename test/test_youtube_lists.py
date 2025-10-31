#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL

from youtube_dl.extractor import (
    YoutubeIE,
    YoutubePlaylistIE,
    YoutubeTabIE,
)


class TestYoutubeLists(unittest.TestCase):
    def assertIsPlaylist(self, info):
        """Make sure the info has '_type' set to 'playlist'"""
        self.assertEqual(info['_type'], 'playlist')

    def test_youtube_playlist_noplaylist(self):
        dl = FakeYDL()
        dl.params['noplaylist'] = True
        dl.params['format'] = 'best'
        ie = YoutubePlaylistIE(dl)
        result = ie.extract('https://www.youtube.com/watch?v=FXxLjLQi3Fg&list=PLwiyx1dc3P2JR9N8gQaQN_BCvlSlap7re')
        self.assertEqual(result['_type'], 'url')
        result = dl.extract_info(result['url'], download=False, ie_key=result.get('ie_key'), process=False)
        self.assertEqual(YoutubeIE().extract_id(result['url']), 'FXxLjLQi3Fg')

    def test_youtube_mix(self):
        dl = FakeYDL()
        dl.params['format'] = 'best'
        ie = YoutubeTabIE(dl)
        result = dl.extract_info('https://www.youtube.com/watch?v=tyITL_exICo&list=RDCLAK5uy_kLWIr9gv1XLlPbaDS965-Db4TrBoUTxQ8',
                                 download=False, ie_key=ie.ie_key(), process=True)
        entries = (result or {}).get('entries', [{'id': 'not_found', }])
        self.assertTrue(len(entries) >= 25)
        original_video = entries[0]
        self.assertEqual(original_video['id'], 'tyITL_exICo')

    def test_youtube_flat_playlist_extraction(self):
        dl = FakeYDL()
        dl.params['extract_flat'] = True
        ie = YoutubeTabIE(dl)
        result = ie.extract('https://www.youtube.com/playlist?list=PL4lCao7KL_QFVb7Iudeipvc2BCavECqzc')
        self.assertIsPlaylist(result)
        entries = list(result['entries'])
        self.assertTrue(len(entries) == 1)
        video = entries[0]
        self.assertEqual(video['_type'], 'url')
        self.assertEqual(video['ie_key'], 'Youtube')
        self.assertEqual(video['id'], 'BaW_jenozKc')
        self.assertEqual(video['url'], 'BaW_jenozKc')
        self.assertEqual(video['title'], 'youtube-dl test video "\'/\\ä↭𝕐')
        self.assertEqual(video['duration'], 10)
        self.assertEqual(video['uploader'], 'Philipp Hagemeister')


if __name__ == '__main__':
    unittest.main()
