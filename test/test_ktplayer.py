#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.extractor.ktplayer import KtPlayerHelper


class TestKtPlayerHelper(unittest.TestCase):
    def test_kt_player_helper_lc(self):
        self.assertEqual(
            KtPlayerHelper._hash_kt_player_lic_code('$385023312702592'),
            '49618502835613441220119020166725')
        self.assertEqual(
            KtPlayerHelper._hash_kt_player_lic_code('$518170117095338'),
            '62924140695851455899788411700698')

    def test_kt_player_helper_hash_convert(self):
        self.assertEqual(
            KtPlayerHelper.convert_video_hash('$385023312702592', 'bed397181d043299c43f63582406a20b'),
            '8b0bdf194430202ed49325c186633a79')
        self.assertEqual(
            KtPlayerHelper.convert_video_hash('$518170117095338', '8b25b576ffbf46fa3dc91e34eddc2190b7d3146586'),
            'f34c6dff1f890e75b6b59422dde3b1acb7d3146586')

    def test_get_url(self):
        page1 = """
        var flashvars = {
            license_code: '$385023312702592',
            video_url: 'http://example.com/get_file/2/bed397181d043299c43f63582406a20b/223000/223101/223101.mp4/',
        }
        """
        self.assertEqual(
            KtPlayerHelper.get_url(page1),
            'http://example.com/get_file/2/8b0bdf194430202ed49325c186633a79/223000/223101/223101.mp4/')

        page2 = """
        var flashvars = {
            license_code: '$518170117095338',
            video_url: 'http://example.com/get_file/2/8b25b576ffbf46fa3dc91e34eddc2190b7d3146586/223000/223101/223101.mp4/',
        }
        """
        self.assertEqual(
            KtPlayerHelper.get_url(page2),
            'http://example.com/get_file/2/f34c6dff1f890e75b6b59422dde3b1acb7d3146586/223000/223101/223101.mp4/')


if __name__ == '__main__':
    unittest.main()
