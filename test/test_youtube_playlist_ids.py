#!/usr/bin/env python

import sys
import unittest

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.InfoExtractors import YoutubeIE, YoutubePlaylistIE

class TestYoutubePlaylistMatching(unittest.TestCase):
    def test_playlist_matching(self):
        self.assertTrue(YoutubePlaylistIE().suitable(u'ECUl4u3cNGP61MdtwGTqZA0MreSaDybji8'))
        self.assertTrue(YoutubePlaylistIE().suitable(u'PL63F0C78739B09958'))
        self.assertFalse(YoutubePlaylistIE().suitable(u'PLtS2H6bU1M'))

    def test_youtube_matching(self):
        self.assertTrue(YoutubeIE().suitable(u'PLtS2H6bU1M'))

if __name__ == '__main__':
    unittest.main()
