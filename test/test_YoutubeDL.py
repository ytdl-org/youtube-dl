#!/usr/bin/env python

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL


class YDL(FakeYDL):
    def __init__(self, *args, **kwargs):
        super(YDL, self).__init__(*args, **kwargs)
        self.downloaded_info_dicts = []
        self.msgs = []

    def process_info(self, info_dict):
        self.downloaded_info_dicts.append(info_dict)

    def to_screen(self, msg):
        self.msgs.append(msg)


class TestFormatSelection(unittest.TestCase):
    def test_prefer_free_formats(self):
        # Same resolution => download webm
        ydl = YDL()
        ydl.params['prefer_free_formats'] = True
        formats = [
            {u'ext': u'webm', u'height': 460},
            {u'ext': u'mp4',  u'height': 460},
        ]
        info_dict = {u'formats': formats, u'extractor': u'test'}
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'ext'], u'webm')

        # Different resolution => download best quality (mp4)
        ydl = YDL()
        ydl.params['prefer_free_formats'] = True
        formats = [
            {u'ext': u'webm', u'height': 720},
            {u'ext': u'mp4', u'height': 1080},
        ]
        info_dict[u'formats'] = formats
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'ext'], u'mp4')

        # No prefer_free_formats => keep original formats order
        ydl = YDL()
        ydl.params['prefer_free_formats'] = False
        formats = [
            {u'ext': u'webm', u'height': 720},
            {u'ext': u'flv', u'height': 720},
        ]
        info_dict[u'formats'] = formats
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'ext'], u'flv')

    def test_format_limit(self):
        formats = [
            {u'format_id': u'meh'},
            {u'format_id': u'good'},
            {u'format_id': u'great'},
            {u'format_id': u'excellent'},
        ]
        info_dict = {
            u'formats': formats, u'extractor': u'test', 'id': 'testvid'}

        ydl = YDL()
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'format_id'], u'excellent')

        ydl = YDL({'format_limit': 'good'})
        assert ydl.params['format_limit'] == 'good'
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'format_id'], u'good')

        ydl = YDL({'format_limit': 'great', 'format': 'all'})
        ydl.process_ie_result(info_dict)
        self.assertEqual(ydl.downloaded_info_dicts[0][u'format_id'], u'meh')
        self.assertEqual(ydl.downloaded_info_dicts[1][u'format_id'], u'good')
        self.assertEqual(ydl.downloaded_info_dicts[2][u'format_id'], u'great')
        self.assertTrue('3' in ydl.msgs[0])

        ydl = YDL()
        ydl.params['format_limit'] = 'excellent'
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'format_id'], u'excellent')

    def test_format_selection(self):
        formats = [
            {u'format_id': u'35', u'ext': u'mp4'},
            {u'format_id': u'45', u'ext': u'webm'},
            {u'format_id': u'47', u'ext': u'webm'},
            {u'format_id': u'2', u'ext': u'flv'},
        ]
        info_dict = {u'formats': formats, u'extractor': u'test'}

        ydl = YDL({'format': u'20/47'})
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], u'47')

        ydl = YDL({'format': u'20/71/worst'})
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], u'35')

        ydl = YDL()
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], u'2')

        ydl = YDL({'format': u'webm/mp4'})
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], u'47')

        ydl = YDL({'format': u'3gp/40/mp4'})
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], u'35')


if __name__ == '__main__':
    unittest.main()
