#!/usr/bin/env python

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.postprocessor import MetadataFromTitlePP


class TestMetadataFromTitle(unittest.TestCase):
    def test_format_to_regex(self):
        pp = MetadataFromTitlePP(None, '%(title)s - %(artist)s')
        self.assertEqual(pp._titleregex, r'(?P<title>.+)\ \-\ (?P<artist>.+)')


class TestEmbedThumbnail(unittest.TestCase):
    def test_run_case_insensitive(self):
        from youtube_dl.postprocessor import EmbedThumbnailPP
        class DummyDownloader(object):
            params = {}
            def to_screen(self, msg):
                pass
        pp = EmbedThumbnailPP(DummyDownloader())

        res_files, res_info = pp.run({'ext': 'MP3', 'filepath': 'file.mp3', 'thumbnails': []})
        self.assertEqual(res_files, [])
        self.assertEqual(res_info['ext'], 'MP3')

        res_files, res_info = pp.run({'ext': 'MP4', 'filepath': 'file.mp4', 'thumbnails': []})
        self.assertEqual(res_files, [])
        self.assertEqual(res_info['ext'], 'MP4')

