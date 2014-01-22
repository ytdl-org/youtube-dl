#!/usr/bin/env python

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL
from youtube_dl import YoutubeDL
from youtube_dl.extractor import YoutubeIE


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
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
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
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'ext'], u'mp4')

        # No prefer_free_formats => prefer mp4 and flv for greater compatibilty
        ydl = YDL()
        ydl.params['prefer_free_formats'] = False
        formats = [
            {u'ext': u'webm', u'height': 720},
            {u'ext': u'mp4', u'height': 720},
            {u'ext': u'flv', u'height': 720},
        ]
        info_dict[u'formats'] = formats
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'ext'], u'mp4')

        ydl = YDL()
        ydl.params['prefer_free_formats'] = False
        formats = [
            {u'ext': u'flv', u'height': 720},
            {u'ext': u'webm', u'height': 720},
        ]
        info_dict[u'formats'] = formats
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'ext'], u'flv')

    def test_format_limit(self):
        formats = [
            {u'format_id': u'meh', u'url': u'http://example.com/meh', 'preference': 1},
            {u'format_id': u'good', u'url': u'http://example.com/good', 'preference': 2},
            {u'format_id': u'great', u'url': u'http://example.com/great', 'preference': 3},
            {u'format_id': u'excellent', u'url': u'http://example.com/exc', 'preference': 4},
        ]
        info_dict = {
            u'formats': formats, u'extractor': u'test', 'id': 'testvid'}

        ydl = YDL()
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'format_id'], u'excellent')

        ydl = YDL({'format_limit': 'good'})
        assert ydl.params['format_limit'] == 'good'
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'format_id'], u'good')

        ydl = YDL({'format_limit': 'great', 'format': 'all'})
        ydl.process_ie_result(info_dict.copy())
        self.assertEqual(ydl.downloaded_info_dicts[0][u'format_id'], u'meh')
        self.assertEqual(ydl.downloaded_info_dicts[1][u'format_id'], u'good')
        self.assertEqual(ydl.downloaded_info_dicts[2][u'format_id'], u'great')
        self.assertTrue('3' in ydl.msgs[0])

        ydl = YDL()
        ydl.params['format_limit'] = 'excellent'
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded[u'format_id'], u'excellent')

    def test_format_selection(self):
        formats = [
            {u'format_id': u'35', u'ext': u'mp4', 'preference': 1},
            {u'format_id': u'45', u'ext': u'webm', 'preference': 2},
            {u'format_id': u'47', u'ext': u'webm', 'preference': 3},
            {u'format_id': u'2', u'ext': u'flv', 'preference': 4},
        ]
        info_dict = {u'formats': formats, u'extractor': u'test'}

        ydl = YDL({'format': u'20/47'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], u'47')

        ydl = YDL({'format': u'20/71/worst'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], u'35')

        ydl = YDL()
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], u'2')

        ydl = YDL({'format': u'webm/mp4'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], u'47')

        ydl = YDL({'format': u'3gp/40/mp4'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], u'35')

    def test_youtube_format_selection(self):
        order = [
            '38', '37', '46', '22', '45', '35', '44', '18', '34', '43', '6', '5', '36', '17', '13',
            # Apple HTTP Live Streaming
            '96', '95', '94', '93', '92', '132', '151',
            # 3D
            '85', '84', '102', '83', '101', '82', '100',
            # Dash video
            '138', '137', '248', '136', '247', '135', '246',
            '245', '244', '134', '243', '133', '242', '160',
            # Dash audio
            '141', '172', '140', '139', '171',
        ]

        for f1id, f2id in zip(order, order[1:]):
            f1 = YoutubeIE._formats[f1id].copy()
            f1['format_id'] = f1id
            f2 = YoutubeIE._formats[f2id].copy()
            f2['format_id'] = f2id

            info_dict = {'formats': [f1, f2], 'extractor': 'youtube'}
            ydl = YDL()
            yie = YoutubeIE(ydl)
            yie._sort_formats(info_dict['formats'])
            ydl.process_ie_result(info_dict)
            downloaded = ydl.downloaded_info_dicts[0]
            self.assertEqual(downloaded['format_id'], f1id)

            info_dict = {'formats': [f2, f1], 'extractor': 'youtube'}
            ydl = YDL()
            yie = YoutubeIE(ydl)
            yie._sort_formats(info_dict['formats'])
            ydl.process_ie_result(info_dict)
            downloaded = ydl.downloaded_info_dicts[0]
            self.assertEqual(downloaded['format_id'], f1id)

    def test_add_extra_info(self):
        test_dict = {
            'extractor': 'Foo',
        }
        extra_info = {
            'extractor': 'Bar',
            'playlist': 'funny videos',
        }
        YDL.add_extra_info(test_dict, extra_info)
        self.assertEqual(test_dict['extractor'], 'Foo')
        self.assertEqual(test_dict['playlist'], 'funny videos')

    def test_prepare_filename(self):
        info = {
            u'id': u'1234',
            u'ext': u'mp4',
            u'width': None,
        }
        def fname(templ):
            ydl = YoutubeDL({'outtmpl': templ})
            return ydl.prepare_filename(info)
        self.assertEqual(fname(u'%(id)s.%(ext)s'), u'1234.mp4')
        self.assertEqual(fname(u'%(id)s-%(width)s.%(ext)s'), u'1234-NA.mp4')
        # Replace missing fields with 'NA'
        self.assertEqual(fname(u'%(uploader_date)s-%(id)s.%(ext)s'), u'NA-1234.mp4')


if __name__ == '__main__':
    unittest.main()
