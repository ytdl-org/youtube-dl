#!/usr/bin/env python

import sys
import unittest

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.InfoExtractors import YoutubeIE, YoutubePlaylistIE

class TestAllURLsMatching(unittest.TestCase):
    def test_youtube_playlist_matching(self):
        self.assertTrue(YoutubePlaylistIE.suitable(u'ECUl4u3cNGP61MdtwGTqZA0MreSaDybji8'))
        self.assertTrue(YoutubePlaylistIE.suitable(u'UUBABnxM4Ar9ten8Mdjj1j0Q')) #585
        self.assertTrue(YoutubePlaylistIE.suitable(u'PL63F0C78739B09958'))
        self.assertTrue(YoutubePlaylistIE.suitable(u'https://www.youtube.com/playlist?list=UUBABnxM4Ar9ten8Mdjj1j0Q'))
        self.assertTrue(YoutubePlaylistIE.suitable(u'https://www.youtube.com/course?list=ECUl4u3cNGP61MdtwGTqZA0MreSaDybji8'))
        self.assertTrue(YoutubePlaylistIE.suitable(u'https://www.youtube.com/playlist?list=PLwP_SiAcdui0KVebT0mU9Apz359a4ubsC'))
        self.assertTrue(YoutubePlaylistIE.suitable(u'https://www.youtube.com/watch?v=AV6J6_AeFEQ&playnext=1&list=PL4023E734DA416012')) #668
        self.assertFalse(YoutubePlaylistIE.suitable(u'PLtS2H6bU1M'))

    def test_youtube_matching(self):
        self.assertTrue(YoutubeIE.suitable(u'PLtS2H6bU1M'))
        self.assertFalse(YoutubeIE.suitable(u'https://www.youtube.com/watch?v=AV6J6_AeFEQ&playnext=1&list=PL4023E734DA416012')) #668

    def test_youtube_extract(self):
        self.assertEqual(YoutubeIE()._extract_id('http://www.youtube.com/watch?&v=BaW_jenozKc'), 'BaW_jenozKc')
        self.assertEqual(YoutubeIE()._extract_id('https://www.youtube.com/watch?&v=BaW_jenozKc'), 'BaW_jenozKc')
        self.assertEqual(YoutubeIE()._extract_id('https://www.youtube.com/watch?feature=player_embedded&v=BaW_jenozKc'), 'BaW_jenozKc')

if __name__ == '__main__':
    unittest.main()
