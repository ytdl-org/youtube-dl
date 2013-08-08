#!/usr/bin/env python

import sys
import unittest
import json

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.extractor import DailymotionPlaylistIE, VimeoChannelIE
from youtube_dl.utils import *

from helper import FakeYDL

class TestPlaylists(unittest.TestCase):
    def assertIsPlaylist(self, info):
        """Make sure the info has '_type' set to 'playlist'"""
        self.assertEqual(info['_type'], 'playlist')

    def test_dailymotion_playlist(self):
        dl = FakeYDL()
        ie = DailymotionPlaylistIE(dl)
        result = ie.extract('http://www.dailymotion.com/playlist/xv4bw_nqtv_sport/1#video=xl8v3q')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], u'SPORT')
        self.assertTrue(len(result['entries']) > 20)

    def test_vimeo_channel(self):
        dl = FakeYDL()
        ie = VimeoChannelIE(dl)
        result = ie.extract('http://vimeo.com/channels/tributes')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], u'Vimeo Tributes')
        self.assertTrue(len(result['entries']) > 24)

if __name__ == '__main__':
    unittest.main()
