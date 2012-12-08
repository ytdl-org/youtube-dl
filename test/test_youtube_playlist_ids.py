#!/usr/bin/env python

import sys
import unittest

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.InfoExtractors import YoutubeIE, YoutubePlaylistIE

class TestYoutubePlaylistMatching(unittest.TestCase):
    def test_playlist_matching(self):
        assert YoutubePlaylistIE().suitable(u'ECUl4u3cNGP61MdtwGTqZA0MreSaDybji8')
        assert YoutubePlaylistIE().suitable(u'PL63F0C78739B09958')
        assert not YoutubePlaylistIE().suitable(u'PLtS2H6bU1M')

    def test_youtube_matching(self):
        assert YoutubeIE().suitable(u'PLtS2H6bU1M')

if __name__ == '__main__':
    unittest.main()
