#!/usr/bin/env python
# coding: utf-8

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import get_params


import io
import json

import youtube_dl.YoutubeDL
import youtube_dl.extractor


class YoutubeDL(youtube_dl.YoutubeDL):
    def __init__(self, *args, **kwargs):
        super(YoutubeDL, self).__init__(*args, **kwargs)
        self.to_stderr = self.to_screen

params = get_params({
    'writeinfojson': True,
    'skip_download': True,
    'writedescription': True,
})


TEST_ID = 'BaW_jenozKc'
INFO_JSON_FILE = TEST_ID + '.info.json'
DESCRIPTION_FILE = TEST_ID + '.mp4.description'
EXPECTED_DESCRIPTION = u'''test chars:  "'/\ä↭𝕐
test URL: https://github.com/rg3/youtube-dl/issues/1892

This is a test video for youtube-dl.

For more information, contact phihag@phihag.de .'''


class TestInfoJSON(unittest.TestCase):
    def setUp(self):
        # Clear old files
        self.tearDown()

    def test_info_json(self):
        ie = youtube_dl.extractor.YoutubeIE()
        ydl = YoutubeDL(params)
        ydl.add_info_extractor(ie)
        ydl.download([TEST_ID])
        self.assertTrue(os.path.exists(INFO_JSON_FILE))
        with io.open(INFO_JSON_FILE, 'r', encoding='utf-8') as jsonf:
            jd = json.load(jsonf)
        self.assertEqual(jd['upload_date'], u'20121002')
        self.assertEqual(jd['description'], EXPECTED_DESCRIPTION)
        self.assertEqual(jd['id'], TEST_ID)
        self.assertEqual(jd['extractor'], 'youtube')
        self.assertEqual(jd['title'], u'''youtube-dl test video "'/\ä↭𝕐''')
        self.assertEqual(jd['uploader'], 'Philipp Hagemeister')

        self.assertTrue(os.path.exists(DESCRIPTION_FILE))
        with io.open(DESCRIPTION_FILE, 'r', encoding='utf-8') as descf:
            descr = descf.read()
        self.assertEqual(descr, EXPECTED_DESCRIPTION)

    def tearDown(self):
        if os.path.exists(INFO_JSON_FILE):
            os.remove(INFO_JSON_FILE)
        if os.path.exists(DESCRIPTION_FILE):
            os.remove(DESCRIPTION_FILE)

if __name__ == '__main__':
    unittest.main()
