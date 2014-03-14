#!/usr/bin/env python

from __future__ import unicode_literals

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
            {'ext': 'webm', 'height': 460},
            {'ext': 'mp4',  'height': 460},
        ]
        info_dict = {'formats': formats, 'extractor': 'test'}
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['ext'], 'webm')

        # Different resolution => download best quality (mp4)
        ydl = YDL()
        ydl.params['prefer_free_formats'] = True
        formats = [
            {'ext': 'webm', 'height': 720},
            {'ext': 'mp4', 'height': 1080},
        ]
        info_dict['formats'] = formats
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['ext'], 'mp4')

        # No prefer_free_formats => prefer mp4 and flv for greater compatibilty
        ydl = YDL()
        ydl.params['prefer_free_formats'] = False
        formats = [
            {'ext': 'webm', 'height': 720},
            {'ext': 'mp4', 'height': 720},
            {'ext': 'flv', 'height': 720},
        ]
        info_dict['formats'] = formats
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['ext'], 'mp4')

        ydl = YDL()
        ydl.params['prefer_free_formats'] = False
        formats = [
            {'ext': 'flv', 'height': 720},
            {'ext': 'webm', 'height': 720},
        ]
        info_dict['formats'] = formats
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['ext'], 'flv')

    def test_format_limit(self):
        formats = [
            {'format_id': 'meh', 'url': 'http://example.com/meh', 'preference': 1},
            {'format_id': 'good', 'url': 'http://example.com/good', 'preference': 2},
            {'format_id': 'great', 'url': 'http://example.com/great', 'preference': 3},
            {'format_id': 'excellent', 'url': 'http://example.com/exc', 'preference': 4},
        ]
        info_dict = {
            'formats': formats, 'extractor': 'test', 'id': 'testvid'}

        ydl = YDL()
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'excellent')

        ydl = YDL({'format_limit': 'good'})
        assert ydl.params['format_limit'] == 'good'
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'good')

        ydl = YDL({'format_limit': 'great', 'format': 'all'})
        ydl.process_ie_result(info_dict.copy())
        self.assertEqual(ydl.downloaded_info_dicts[0]['format_id'], 'meh')
        self.assertEqual(ydl.downloaded_info_dicts[1]['format_id'], 'good')
        self.assertEqual(ydl.downloaded_info_dicts[2]['format_id'], 'great')
        self.assertTrue('3' in ydl.msgs[0])

        ydl = YDL()
        ydl.params['format_limit'] = 'excellent'
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'excellent')

    def test_format_selection(self):
        formats = [
            {'format_id': '35', 'ext': 'mp4', 'preference': 1},
            {'format_id': '45', 'ext': 'webm', 'preference': 2},
            {'format_id': '47', 'ext': 'webm', 'preference': 3},
            {'format_id': '2', 'ext': 'flv', 'preference': 4},
        ]
        info_dict = {'formats': formats, 'extractor': 'test'}

        ydl = YDL({'format': '20/47'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], '47')

        ydl = YDL({'format': '20/71/worst'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], '35')

        ydl = YDL()
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], '2')

        ydl = YDL({'format': 'webm/mp4'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], '47')

        ydl = YDL({'format': '3gp/40/mp4'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], '35')

    def test_format_selection_audio(self):
        formats = [
            {'format_id': 'audio-low', 'ext': 'webm', 'preference': 1, 'vcodec': 'none'},
            {'format_id': 'audio-mid', 'ext': 'webm', 'preference': 2, 'vcodec': 'none'},
            {'format_id': 'audio-high', 'ext': 'flv', 'preference': 3, 'vcodec': 'none'},
            {'format_id': 'vid', 'ext': 'mp4', 'preference': 4},
        ]
        info_dict = {'formats': formats, 'extractor': 'test'}

        ydl = YDL({'format': 'bestaudio'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'audio-high')

        ydl = YDL({'format': 'worstaudio'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'audio-low')

        formats = [
            {'format_id': 'vid-low', 'ext': 'mp4', 'preference': 1},
            {'format_id': 'vid-high', 'ext': 'mp4', 'preference': 2},
        ]
        info_dict = {'formats': formats, 'extractor': 'test'}

        ydl = YDL({'format': 'bestaudio/worstaudio/best'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'vid-high')

    def test_format_selection_video(self):
        formats = [
            {'format_id': 'dash-video-low', 'ext': 'mp4', 'preference': 1, 'acodec': 'none'},
            {'format_id': 'dash-video-high', 'ext': 'mp4', 'preference': 2, 'acodec': 'none'},
            {'format_id': 'vid', 'ext': 'mp4', 'preference': 3},
        ]
        info_dict = {'formats': formats, 'extractor': 'test'}

        ydl = YDL({'format': 'bestvideo'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'dash-video-high')

        ydl = YDL({'format': 'worstvideo'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'dash-video-low')

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
            'id': '1234',
            'ext': 'mp4',
            'width': None,
        }
        def fname(templ):
            ydl = YoutubeDL({'outtmpl': templ})
            return ydl.prepare_filename(info)
        self.assertEqual(fname('%(id)s.%(ext)s'), '1234.mp4')
        self.assertEqual(fname('%(id)s-%(width)s.%(ext)s'), '1234-NA.mp4')
        # Replace missing fields with 'NA'
        self.assertEqual(fname('%(uploader_date)s-%(id)s.%(ext)s'), 'NA-1234.mp4')


if __name__ == '__main__':
    unittest.main()
