#!/usr/bin/env python
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import try_rm

from youtube_dl import YoutubeDL

class TestMetacafeFFilter(unittest.TestCase):
    def test_metacafe(self):
        filename = '2155630.mp4'
        url = 'http://www.metacafe.com/watch/2155630/adult_art_by_david_hart_156/'

        params = {
            'skip_download': True,
            'writeinfojson': True,
            'outtmpl': '%(id)s.%(ext)s',
        }
        ydl = YoutubeDL(params)
        ydl.add_default_info_extractors()
        json_filename = os.path.splitext(filename)[0] + '.info.json'
        try_rm(json_filename)
        ydl.download([url])
        res = os.path.exists(json_filename)
        try_rm(json_filename)
        self.assertTrue(res)


if __name__ == '__main__':
    unittest.main()
