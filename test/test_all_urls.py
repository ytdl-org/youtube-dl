#!/usr/bin/env python

import sys
import unittest

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.InfoExtractors import YoutubeIE, YoutubePlaylistIE

class TestAllURLsMatching(unittest.TestCase):
    def test_youtube_playlist_matching(self):
        self.assertTrue(YoutubePlaylistIE().suitable(u'ECUl4u3cNGP61MdtwGTqZA0MreSaDybji8'))
        self.assertTrue(YoutubePlaylistIE().suitable(u'PL63F0C78739B09958'))
        self.assertFalse(YoutubePlaylistIE().suitable(u'PLtS2H6bU1M'))

    def test_youtube_matching(self):
        self.assertTrue(YoutubeIE().suitable(u'PLtS2H6bU1M'))

    def test_youtube_extract(self):
        self.assertEqual(YoutubeIE()._extract_id('http://www.youtube.com/watch?&v=BaW_jenozKc'), 'BaW_jenozKc')
        self.assertEqual(YoutubeIE()._extract_id('https://www.youtube.com/watch?&v=BaW_jenozKc'), 'BaW_jenozKc')
        self.assertEqual(YoutubeIE()._extract_id('https://www.youtube.com/watch?feature=player_embedded&v=BaW_jenozKc'), 'BaW_jenozKc')

if __name__ == '__main__':
    unittest.main()
