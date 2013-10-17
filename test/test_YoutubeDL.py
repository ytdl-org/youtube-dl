#!/usr/bin/env python

import sys
import unittest

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helper import FakeYDL, parameters

class YDL(FakeYDL):
    def __init__(self):
        super(YDL, self).__init__()
        self.downloaded_info_dicts = []
    def process_info(self, info_dict):
        self.downloaded_info_dicts.append(info_dict)

class TestFormatSelection(unittest.TestCase):
    def test_prefer_free_formats(self):
        # Same resolution => download webm
        ydl = YDL()
        ydl.params['prefer_free_formats'] = True
        formats = [{u'ext': u'webm', u'height': 460},{u'ext': u'mp4',  u'height': 460}]
        info_dict = {u'formats': formats, u'extractor': u'test'}
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'ext'], u'webm')

        # Different resolution => download best quality (mp4)
        ydl = YDL()
        ydl.params['prefer_free_formats'] = True
        formats = [{u'ext': u'webm', u'height': 720},{u'ext': u'mp4',u'height': 1080}]
        info_dict[u'formats'] = formats
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'ext'], u'mp4')

        # No prefer_free_formats => keep original formats order
        ydl = YDL()
        ydl.params['prefer_free_formats'] = False
        formats = [{u'ext': u'webm', u'height': 720},{u'ext': u'flv',u'height': 720}]
        info_dict[u'formats'] = formats
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'ext'], u'flv')

if __name__ == '__main__':
    unittest.main()
