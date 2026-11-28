#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import copy
import json

from test.helper import (
    FakeYDL,
    assertRegexpMatches,
    try_rm,
)
from youtube_dl import YoutubeDL
from youtube_dl.compat import (
    compat_http_cookiejar_Cookie,
    compat_http_cookies_SimpleCookie,
    compat_kwargs,
    compat_open as open,
    compat_str,
    compat_urllib_error,
)

from youtube_dl.extractor import YoutubeIE
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.postprocessor.common import PostProcessor
from youtube_dl.utils import (
    ExtractorError,
    match_filter_func,
    traverse_obj,
)

TEST_URL = 'http://localhost/sample.mp4'


class YDL(FakeYDL):
    def __init__(self, *args, **kwargs):
        super(YDL, self).__init__(*args, **kwargs)
        self.downloaded_info_dicts = []
        self.msgs = []

    def process_info(self, info_dict):
        self.downloaded_info_dicts.append(info_dict.copy())

    def to_screen(self, msg):
        self.msgs.append(msg)

    def dl(self, *args, **kwargs):
        assert False, 'Downloader must not be invoked for test_YoutubeDL'


def _make_result(formats, **kwargs):
    res = {
        'formats': formats,
        'id': 'testid',
        'title': 'testttitle',
        'extractor': 'testex',
        'extractor_key': 'TestEx',
        'webpage_url': 'http://example.com/watch?v=shenanigans',
    }
    res.update(**compat_kwargs(kwargs))
    return res


class TestFormatSelection(unittest.TestCase):
    def test_prefer_free_formats(self):
        # Same resolution => download webm
        ydl = YDL()
        ydl.params['prefer_free_formats'] = True
        formats = [
            {'ext': 'webm', 'height': 460, 'url': TEST_URL},
            {'ext': 'mp4', 'height': 460, 'url': TEST_URL},
        ]
        info_dict = _make_result(formats)
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['ext'], 'webm')

        # Different resolution => download best quality (mp4)
        ydl = YDL()
        ydl.params['prefer_free_formats'] = True
        formats = [
            {'ext': 'webm', 'height': 720, 'url': TEST_URL},
            {'ext': 'mp4', 'height': 1080, 'url': TEST_URL},
        ]
        info_dict['formats'] = formats
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['ext'], 'mp4')

        # No prefer_free_formats => prefer mp4 and flv for greater compatibility
        ydl = YDL()
        ydl.params['prefer_free_formats'] = False
        formats = [
            {'ext': 'webm', 'height': 720, 'url': TEST_URL},
            {'ext': 'mp4', 'height': 720, 'url': TEST_URL},
            {'ext': 'flv', 'height': 720, 'url': TEST_URL},
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
            {'ext': 'flv', 'height': 720, 'url': TEST_URL},
            {'ext': 'webm', 'height': 720, 'url': TEST_URL},
        ]
        info_dict['formats'] = formats
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['ext'], 'flv')

    def test_format_selection(self):
        formats = [
            {'format_id': '35', 'ext': 'mp4', 'preference': 1, 'url': TEST_URL},
            {'format_id': 'example-with-dashes', 'ext': 'webm', 'preference': 1, 'url': TEST_URL},
            {'format_id': '45', 'ext': 'webm', 'preference': 2, 'url': TEST_URL},
            {'format_id': '47', 'ext': 'webm', 'preference': 3, 'url': TEST_URL},
            {'format_id': '2', 'ext': 'flv', 'preference': 4, 'url': TEST_URL},
        ]
        info_dict = _make_result(formats)

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

        ydl = YDL({'format': 'example-with-dashes'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'example-with-dashes')

    def test_format_selection_audio(self):
        formats = [
            {'format_id': 'audio-low', 'ext': 'webm', 'preference': 1, 'vcodec': 'none', 'url': TEST_URL},
            {'format_id': 'audio-mid', 'ext': 'webm', 'preference': 2, 'vcodec': 'none', 'url': TEST_URL},
            {'format_id': 'audio-high', 'ext': 'flv', 'preference': 3, 'vcodec': 'none', 'url': TEST_URL},
            {'format_id': 'vid', 'ext': 'mp4', 'preference': 4, 'url': TEST_URL},
        ]
        info_dict = _make_result(formats)

        ydl = YDL({'format': 'bestaudio'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'audio-high')

        ydl = YDL({'format': 'worstaudio'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'audio-low')

        formats = [
            {'format_id': 'vid-low', 'ext': 'mp4', 'preference': 1, 'url': TEST_URL},
            {'format_id': 'vid-high', 'ext': 'mp4', 'preference': 2, 'url': TEST_URL},
        ]
        info_dict = _make_result(formats)

        ydl = YDL({'format': 'bestaudio/worstaudio/best'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'vid-high')

    def test_format_selection_audio_exts(self):
        formats = [
            {'format_id': 'mp3-64', 'ext': 'mp3', 'abr': 64, 'url': 'http://_', 'vcodec': 'none'},
            {'format_id': 'ogg-64', 'ext': 'ogg', 'abr': 64, 'url': 'http://_', 'vcodec': 'none'},
            {'format_id': 'aac-64', 'ext': 'aac', 'abr': 64, 'url': 'http://_', 'vcodec': 'none'},
            {'format_id': 'mp3-32', 'ext': 'mp3', 'abr': 32, 'url': 'http://_', 'vcodec': 'none'},
            {'format_id': 'aac-32', 'ext': 'aac', 'abr': 32, 'url': 'http://_', 'vcodec': 'none'},
        ]

        info_dict = _make_result(formats)
        ydl = YDL({'format': 'best'})
        ie = YoutubeIE(ydl)
        ie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(copy.deepcopy(info_dict))
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'aac-64')

        ydl = YDL({'format': 'mp3'})
        ie = YoutubeIE(ydl)
        ie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(copy.deepcopy(info_dict))
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'mp3-64')

        ydl = YDL({'prefer_free_formats': True})
        ie = YoutubeIE(ydl)
        ie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(copy.deepcopy(info_dict))
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'ogg-64')

    def test_format_selection_video(self):
        formats = [
            {'format_id': 'dash-video-low', 'ext': 'mp4', 'preference': 1, 'acodec': 'none', 'url': TEST_URL},
            {'format_id': 'dash-video-high', 'ext': 'mp4', 'preference': 2, 'acodec': 'none', 'url': TEST_URL},
            {'format_id': 'vid', 'ext': 'mp4', 'preference': 3, 'url': TEST_URL},
        ]
        info_dict = _make_result(formats)

        ydl = YDL({'format': 'bestvideo'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'dash-video-high')

        ydl = YDL({'format': 'worstvideo'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'dash-video-low')

        ydl = YDL({'format': 'bestvideo[format_id^=dash][format_id$=low]'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'dash-video-low')

        formats = [
            {'format_id': 'vid-vcodec-dot', 'ext': 'mp4', 'preference': 1, 'vcodec': 'avc1.123456', 'acodec': 'none', 'url': TEST_URL},
        ]
        info_dict = _make_result(formats)

        ydl = YDL({'format': 'bestvideo[vcodec=avc1.123456]'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'vid-vcodec-dot')

    def test_format_selection_string_ops(self):
        formats = [
            {'format_id': 'abc-cba', 'ext': 'mp4', 'url': TEST_URL},
            {'format_id': 'zxc-cxz', 'ext': 'webm', 'url': TEST_URL},
        ]
        info_dict = _make_result(formats)

        # equals (=)
        ydl = YDL({'format': '[format_id=abc-cba]'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'abc-cba')

        # does not equal (!=)
        ydl = YDL({'format': '[format_id!=abc-cba]'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'zxc-cxz')

        ydl = YDL({'format': '[format_id!=abc-cba][format_id!=zxc-cxz]'})
        self.assertRaises(ExtractorError, ydl.process_ie_result, info_dict.copy())

        # starts with (^=)
        ydl = YDL({'format': '[format_id^=abc]'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'abc-cba')

        # does not start with (!^=)
        ydl = YDL({'format': '[format_id!^=abc]'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'zxc-cxz')

        ydl = YDL({'format': '[format_id!^=abc][format_id!^=zxc]'})
        self.assertRaises(ExtractorError, ydl.process_ie_result, info_dict.copy())

        # ends with ($=)
        ydl = YDL({'format': '[format_id$=cba]'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'abc-cba')

        # does not end with (!$=)
        ydl = YDL({'format': '[format_id!$=cba]'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'zxc-cxz')

        ydl = YDL({'format': '[format_id!$=cba][format_id!$=cxz]'})
        self.assertRaises(ExtractorError, ydl.process_ie_result, info_dict.copy())

        # contains (*=)
        ydl = YDL({'format': '[format_id*=bc-cb]'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'abc-cba')

        # does not contain (!*=)
        ydl = YDL({'format': '[format_id!*=bc-cb]'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'zxc-cxz')

        ydl = YDL({'format': '[format_id!*=abc][format_id!*=zxc]'})
        self.assertRaises(ExtractorError, ydl.process_ie_result, info_dict.copy())

        ydl = YDL({'format': '[format_id!*=-]'})
        self.assertRaises(ExtractorError, ydl.process_ie_result, info_dict.copy())

    def test_youtube_format_selection(self):
        order = [
            '38', '37', '46', '22', '45', '35', '44', '18', '34', '43', '6', '5', '17', '36', '13',
            # Apple HTTP Live Streaming
            '96', '95', '94', '93', '92', '132', '151',
            # 3D
            '85', '84', '102', '83', '101', '82', '100',
            # Dash video
            '137', '248', '136', '247', '135', '246',
            '245', '244', '134', '243', '133', '242', '160',
            # Dash audio
            '141', '172', '140', '171', '139',
        ]

        def format_info(f_id):
            info = YoutubeIE._formats[f_id].copy()

            # XXX: In real cases InfoExtractor._parse_mpd_formats() fills up 'acodec'
            # and 'vcodec', while in tests such information is incomplete since
            # commit a6c2c24479e5f4827ceb06f64d855329c0a6f593
            # test_YoutubeDL.test_youtube_format_selection is broken without
            # this fix
            if 'acodec' in info and 'vcodec' not in info:
                info['vcodec'] = 'none'
            elif 'vcodec' in info and 'acodec' not in info:
                info['acodec'] = 'none'

            info['format_id'] = f_id
            info['url'] = 'url:' + f_id
            return info
        formats_order = [format_info(f_id) for f_id in order]

        info_dict = _make_result(list(formats_order), extractor='youtube')
        ydl = YDL({'format': 'bestvideo+bestaudio'})
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], '137+141')
        self.assertEqual(downloaded['ext'], 'mp4')

        info_dict = _make_result(list(formats_order), extractor='youtube')
        ydl = YDL({'format': 'bestvideo[height>=999999]+bestaudio/best'})
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], '38')

        info_dict = _make_result(list(formats_order), extractor='youtube')
        ydl = YDL({'format': 'bestvideo/best,bestaudio'})
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded_ids = [info['format_id'] for info in ydl.downloaded_info_dicts]
        self.assertEqual(downloaded_ids, ['137', '141'])

        info_dict = _make_result(list(formats_order), extractor='youtube')
        ydl = YDL({'format': '(bestvideo[ext=mp4],bestvideo[ext=webm])+bestaudio'})
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded_ids = [info['format_id'] for info in ydl.downloaded_info_dicts]
        self.assertEqual(downloaded_ids, ['137+141', '248+141'])

        info_dict = _make_result(list(formats_order), extractor='youtube')
        ydl = YDL({'format': '(bestvideo[ext=mp4],bestvideo[ext=webm])[height<=720]+bestaudio'})
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded_ids = [info['format_id'] for info in ydl.downloaded_info_dicts]
        self.assertEqual(downloaded_ids, ['136+141', '247+141'])

        info_dict = _make_result(list(formats_order), extractor='youtube')
        ydl = YDL({'format': '(bestvideo[ext=none]/bestvideo[ext=webm])+bestaudio'})
        yie = YoutubeIE(ydl)
        yie._sort_formats(info_dict['formats'])
        ydl.process_ie_result(info_dict)
        downloaded_ids = [info['format_id'] for info in ydl.downloaded_info_dicts]
        self.assertEqual(downloaded_ids, ['248+141'])

        for f1, f2 in zip(formats_order, formats_order[1:]):
            info_dict = _make_result([f1, f2], extractor='youtube')
            ydl = YDL({'format': 'best/bestvideo'})
            yie = YoutubeIE(ydl)
            yie._sort_formats(info_dict['formats'])
            ydl.process_ie_result(info_dict)
            downloaded = ydl.downloaded_info_dicts[0]
            self.assertEqual(downloaded['format_id'], f1['format_id'])

            info_dict = _make_result([f2, f1], extractor='youtube')
            ydl = YDL({'format': 'best/bestvideo'})
            yie = YoutubeIE(ydl)
            yie._sort_formats(info_dict['formats'])
            ydl.process_ie_result(info_dict)
            downloaded = ydl.downloaded_info_dicts[0]
            self.assertEqual(downloaded['format_id'], f1['format_id'])

    def test_audio_only_extractor_format_selection(self):
        # For extractors with incomplete formats (all formats are audio-only or
        # video-only) best and worst should fallback to corresponding best/worst
        # video-only or audio-only formats (as per
        # https://github.com/ytdl-org/youtube-dl/pull/5556)
        formats = [
            {'format_id': 'low', 'ext': 'mp3', 'preference': 1, 'vcodec': 'none', 'url': TEST_URL},
            {'format_id': 'high', 'ext': 'mp3', 'preference': 2, 'vcodec': 'none', 'url': TEST_URL},
        ]
        info_dict = _make_result(formats)

        ydl = YDL({'format': 'best'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'high')

        ydl = YDL({'format': 'worst'})
        ydl.process_ie_result(info_dict.copy())
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'low')

    def test_format_not_available(self):
        formats = [
            {'format_id': 'regular', 'ext': 'mp4', 'height': 360, 'url': TEST_URL},
            {'format_id': 'video', 'ext': 'mp4', 'height': 720, 'acodec': 'none', 'url': TEST_URL},
        ]
        info_dict = _make_result(formats)

        # This must fail since complete video-audio format does not match filter
        # and extractor does not provide incomplete only formats (i.e. only
        # video-only or audio-only).
        ydl = YDL({'format': 'best[height>360]'})
        self.assertRaises(ExtractorError, ydl.process_ie_result, info_dict.copy())

    def test_format_selection_issue_10083(self):
        # See https://github.com/ytdl-org/youtube-dl/issues/10083
        formats = [
            {'format_id': 'regular', 'height': 360, 'url': TEST_URL},
            {'format_id': 'video', 'height': 720, 'acodec': 'none', 'url': TEST_URL},
            {'format_id': 'audio', 'vcodec': 'none', 'url': TEST_URL},
        ]
        info_dict = _make_result(formats)

        ydl = YDL({'format': 'best[height>360]/bestvideo[height>360]+bestaudio'})
        ydl.process_ie_result(info_dict.copy())
        self.assertEqual(ydl.downloaded_info_dicts[0]['format_id'], 'video+audio')

    def test_invalid_format_specs(self):
        def assert_syntax_error(format_spec):
            ydl = YDL({'format': format_spec})
            info_dict = _make_result([{'format_id': 'foo', 'url': TEST_URL}])
            self.assertRaises(SyntaxError, ydl.process_ie_result, info_dict)

        assert_syntax_error('bestvideo,,best')
        assert_syntax_error('+bestaudio')
        assert_syntax_error('bestvideo+')
        assert_syntax_error('/')
        assert_syntax_error('bestvideo+bestvideo+bestaudio')

    def test_format_filtering(self):
        formats = [
            {'format_id': 'A', 'filesize': 500, 'width': 1000},
            {'format_id': 'B', 'filesize': 1000, 'width': 500},
            {'format_id': 'C', 'filesize': 1000, 'width': 400},
            {'format_id': 'D', 'filesize': 2000, 'width': 600},
            {'format_id': 'E', 'filesize': 3000},
            {'format_id': 'F'},
            {'format_id': 'G', 'filesize': 1000000},
        ]
        for f in formats:
            f['url'] = 'http://_/'
            f['ext'] = 'unknown'
        info_dict = _make_result(formats)

        ydl = YDL({'format': 'best[filesize<3000]'})
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'D')

        ydl = YDL({'format': 'best[filesize<=3000]'})
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'E')

        ydl = YDL({'format': 'best[filesize <= ? 3000]'})
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'F')

        ydl = YDL({'format': 'best [filesize = 1000] [width>450]'})
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'B')

        ydl = YDL({'format': 'best [filesize = 1000] [width!=450]'})
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'C')

        ydl = YDL({'format': '[filesize>?1]'})
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'G')

        ydl = YDL({'format': '[filesize<1M]'})
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'E')

        ydl = YDL({'format': '[filesize<1MiB]'})
        ydl.process_ie_result(info_dict)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['format_id'], 'G')

        ydl = YDL({'format': 'all[width>=400][width<=600]'})
        ydl.process_ie_result(info_dict)
        downloaded_ids = [info['format_id'] for info in ydl.downloaded_info_dicts]
        self.assertEqual(downloaded_ids, ['B', 'C', 'D'])

        ydl = YDL({'format': 'best[height<40]'})
        try:
            ydl.process_ie_result(info_dict)
        except ExtractorError:
            pass
        self.assertEqual(ydl.downloaded_info_dicts, [])

    def test_default_format_spec(self):
        ydl = YDL({'simulate': True})
        self.assertEqual(ydl._default_format_spec({}), 'bestvideo+bestaudio/best')

        ydl = YDL({})
        self.assertEqual(ydl._default_format_spec({'is_live': True}), 'best/bestvideo+bestaudio')

        ydl = YDL({'simulate': True})
        self.assertEqual(ydl._default_format_spec({'is_live': True}), 'bestvideo+bestaudio/best')

        ydl = YDL({'outtmpl': '-'})
        self.assertEqual(ydl._default_format_spec({}), 'best/bestvideo+bestaudio')

        ydl = YDL({})
        self.assertEqual(ydl._default_format_spec({}, download=False), 'bestvideo+bestaudio/best')
        self.assertEqual(ydl._default_format_spec({'is_live': True}), 'best/bestvideo+bestaudio')


class TestYoutubeDL(unittest.TestCase):
    def test_subtitles(self):
        def s_formats(lang, autocaption=False):
            return [{
                'ext': ext,
                'url': 'http://localhost/video.%s.%s' % (lang, ext),
                '_auto': autocaption,
            } for ext in ['vtt', 'srt', 'ass']]
        subtitles = dict((l, s_formats(l)) for l in ['en', 'fr', 'es'])
        auto_captions = dict((l, s_formats(l, True)) for l in ['it', 'pt', 'es'])
        info_dict = {
            'id': 'test',
            'title': 'Test',
            'url': 'http://localhost/video.mp4',
            'subtitles': subtitles,
            'automatic_captions': auto_captions,
            'extractor': 'TEST',
        }

        def get_info(params={}):
            params.setdefault('simulate', True)
            ydl = YDL(params)
            ydl.report_warning = lambda *args, **kargs: None
            return ydl.process_video_result(info_dict, download=False)

        result = get_info()
        self.assertFalse(result.get('requested_subtitles'))
        self.assertEqual(result['subtitles'], subtitles)
        self.assertEqual(result['automatic_captions'], auto_captions)

        result = get_info({'writesubtitles': True})
        subs = result['requested_subtitles']
        self.assertTrue(subs)
        self.assertEqual(set(subs.keys()), set(['en']))
        self.assertTrue(subs['en'].get('data') is None)
        self.assertEqual(subs['en']['ext'], 'ass')

        result = get_info({'writesubtitles': True, 'subtitlesformat': 'foo/srt'})
        subs = result['requested_subtitles']
        self.assertEqual(subs['en']['ext'], 'srt')

        result = get_info({'writesubtitles': True, 'subtitleslangs': ['es', 'fr', 'it']})
        subs = result['requested_subtitles']
        self.assertTrue(subs)
        self.assertEqual(set(subs.keys()), set(['es', 'fr']))

        result = get_info({'writesubtitles': True, 'writeautomaticsub': True, 'subtitleslangs': ['es', 'pt']})
        subs = result['requested_subtitles']
        self.assertTrue(subs)
        self.assertEqual(set(subs.keys()), set(['es', 'pt']))
        self.assertFalse(subs['es']['_auto'])
        self.assertTrue(subs['pt']['_auto'])

        result = get_info({'writeautomaticsub': True, 'subtitleslangs': ['es', 'pt']})
        subs = result['requested_subtitles']
        self.assertTrue(subs)
        self.assertEqual(set(subs.keys()), set(['es', 'pt']))
        self.assertTrue(subs['es']['_auto'])
        self.assertTrue(subs['pt']['_auto'])

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
            'height': 1080,
            'title1': '$PATH',
            'title2': '%PATH%',
            'track': '-track with initial hyphen',
            'display_id': '-initial_hyphen',
            'episode': '.episode with initial period',
            'episode_id': '.initial_period',
        }

        def fname(templ, na_placeholder='NA'):
            params = {'outtmpl': templ}
            if na_placeholder != 'NA':
                params['outtmpl_na_placeholder'] = na_placeholder
            ydl = YoutubeDL(params)
            return ydl.prepare_filename(info)
        self.assertEqual(fname('%(id)s.%(ext)s'), '1234.mp4')
        self.assertEqual(fname('%(id)s-%(width)s.%(ext)s'), '1234-NA.mp4')
        NA_TEST_OUTTMPL = '%(uploader_date)s-%(width)d-%(id)s.%(ext)s'
        # Replace missing fields with 'NA' by default
        self.assertEqual(fname(NA_TEST_OUTTMPL), 'NA-NA-1234.mp4')
        # Or by provided placeholder
        self.assertEqual(fname(NA_TEST_OUTTMPL, na_placeholder='none'), 'none-none-1234.mp4')
        self.assertEqual(fname(NA_TEST_OUTTMPL, na_placeholder=''), '_-1234.mp4')
        NA_TEST_OUTTMPL = '%(uploader_date)s+%(width)d+%(id)s.%(ext)s'
        self.assertEqual(fname(NA_TEST_OUTTMPL, na_placeholder=''), '++1234.mp4')
        self.assertEqual(fname('%(height)d.%(ext)s'), '1080.mp4')
        self.assertEqual(fname('%(height)6d.%(ext)s'), '  1080.mp4')
        self.assertEqual(fname('%(height)-6d.%(ext)s'), '1080  .mp4')
        self.assertEqual(fname('%(height)06d.%(ext)s'), '001080.mp4')
        self.assertEqual(fname('%(height) 06d.%(ext)s'), ' 01080.mp4')
        self.assertEqual(fname('%(height)   06d.%(ext)s'), ' 01080.mp4')
        self.assertEqual(fname('%(height)0 6d.%(ext)s'), ' 01080.mp4')
        self.assertEqual(fname('%(height)0   6d.%(ext)s'), ' 01080.mp4')
        self.assertEqual(fname('%(height)   0   6d.%(ext)s'), ' 01080.mp4')
        self.assertEqual(fname('%%'), '%')
        self.assertEqual(fname('%%%%'), '%%')
        self.assertEqual(fname('%%(height)06d.%(ext)s'), '%(height)06d.mp4')
        self.assertEqual(fname('%(width)06d.%(ext)s'), 'NA.mp4')
        self.assertEqual(fname('%(width)06d.%%(ext)s'), 'NA.%(ext)s')
        self.assertEqual(fname('%%(width)06d.%(ext)s'), '%(width)06d.mp4')
        self.assertEqual(fname('Hello %(title1)s'), 'Hello $PATH')
        self.assertEqual(fname('Hello %(title2)s'), 'Hello %PATH%')
        self.assertEqual(fname('%(track)s at start changes hyphen'),
                         '_track with initial hyphen at start changes hyphen')
        self.assertEqual(fname('medial %(track)s doesn\'t change hyphen'),
                         'medial -track with initial hyphen doesn\'t change hyphen')
        self.assertEqual(fname('%(display_id)s at start doesn\'t change hyphen'),
                         '-initial_hyphen at start doesn\'t change hyphen')
        self.assertEqual(fname('%(episode)s at start changes period'),
                         '_episode with initial period at start changes period')
        self.assertEqual(fname('%(episode_id)s at start doesn\'t change period'),
                         '.initial_period at start doesn\'t change period')

    def test_format_note(self):
        ydl = YoutubeDL()
        self.assertEqual(ydl._format_note({}), '')
        assertRegexpMatches(self, ydl._format_note({
            'vbr': 10,
        }), r'^\s*10k$')
        assertRegexpMatches(self, ydl._format_note({
            'fps': 30,
        }), r'^30fps$')

    def test_postprocessors(self):
        filename = 'post-processor-testfile.mp4'
        audiofile = filename + '.mp3'

        class SimplePP(PostProcessor):
            def run(self, info):
                with open(audiofile, 'w') as f:
                    f.write('EXAMPLE')
                return [info['filepath']], info

        def run_pp(params, PP):
            with open(filename, 'w') as f:
                f.write('EXAMPLE')
            ydl = YoutubeDL(params)
            ydl.add_post_processor(PP())
            ydl.post_process(filename, {'filepath': filename})

        run_pp({'keepvideo': True}, SimplePP)
        self.assertTrue(os.path.exists(filename), '%s doesn\'t exist' % filename)
        self.assertTrue(os.path.exists(audiofile), '%s doesn\'t exist' % audiofile)
        os.unlink(filename)
        os.unlink(audiofile)

        run_pp({'keepvideo': False}, SimplePP)
        self.assertFalse(os.path.exists(filename), '%s exists' % filename)
        self.assertTrue(os.path.exists(audiofile), '%s doesn\'t exist' % audiofile)
        os.unlink(audiofile)

        class ModifierPP(PostProcessor):
            def run(self, info):
                with open(info['filepath'], 'w') as f:
                    f.write('MODIFIED')
                return [], info

        run_pp({'keepvideo': False}, ModifierPP)
        self.assertTrue(os.path.exists(filename), '%s doesn\'t exist' % filename)
        os.unlink(filename)

    def test_match_filter(self):
        class FilterYDL(YDL):
            def __init__(self, *args, **kwargs):
                super(FilterYDL, self).__init__(*args, **kwargs)
                self.params['simulate'] = True

            def process_info(self, info_dict):
                super(YDL, self).process_info(info_dict)

            def _match_entry(self, info_dict, incomplete):
                res = super(FilterYDL, self)._match_entry(info_dict, incomplete)
                if res is None:
                    self.downloaded_info_dicts.append(info_dict)
                return res

        first = {
            'id': '1',
            'url': TEST_URL,
            'title': 'one',
            'extractor': 'TEST',
            'duration': 30,
            'filesize': 10 * 1024,
            'playlist_id': '42',
            'uploader': "變態妍字幕版 太妍 тест",
            'creator': "тест ' 123 ' тест--",
        }
        second = {
            'id': '2',
            'url': TEST_URL,
            'title': 'two',
            'extractor': 'TEST',
            'duration': 10,
            'description': 'foo',
            'filesize': 5 * 1024,
            'playlist_id': '43',
            'uploader': "тест 123",
        }
        videos = [first, second]

        def get_videos(filter_=None):
            ydl = FilterYDL({'match_filter': filter_})
            for v in videos:
                ydl.process_ie_result(v, download=True)
            return [v['id'] for v in ydl.downloaded_info_dicts]

        res = get_videos()
        self.assertEqual(res, ['1', '2'])

        def f(v):
            if v['id'] == '1':
                return None
            else:
                return 'Video id is not 1'
        res = get_videos(f)
        self.assertEqual(res, ['1'])

        f = match_filter_func('duration < 30')
        res = get_videos(f)
        self.assertEqual(res, ['2'])

        f = match_filter_func('description = foo')
        res = get_videos(f)
        self.assertEqual(res, ['2'])

        f = match_filter_func('description =? foo')
        res = get_videos(f)
        self.assertEqual(res, ['1', '2'])

        f = match_filter_func('filesize > 5KiB')
        res = get_videos(f)
        self.assertEqual(res, ['1'])

        f = match_filter_func('playlist_id = 42')
        res = get_videos(f)
        self.assertEqual(res, ['1'])

        f = match_filter_func('uploader = "變態妍字幕版 太妍 тест"')
        res = get_videos(f)
        self.assertEqual(res, ['1'])

        f = match_filter_func('uploader != "變態妍字幕版 太妍 тест"')
        res = get_videos(f)
        self.assertEqual(res, ['2'])

        f = match_filter_func('creator = "тест \' 123 \' тест--"')
        res = get_videos(f)
        self.assertEqual(res, ['1'])

        f = match_filter_func("creator = 'тест \\' 123 \\' тест--'")
        res = get_videos(f)
        self.assertEqual(res, ['1'])

        f = match_filter_func(r"creator = 'тест \' 123 \' тест--' & duration > 30")
        res = get_videos(f)
        self.assertEqual(res, [])

    def test_playlist_items_selection(self):
        entries = [{
            'id': compat_str(i),
            'title': compat_str(i),
            'url': TEST_URL,
        } for i in range(1, 5)]
        playlist = {
            '_type': 'playlist',
            'id': 'test',
            'entries': entries,
            'extractor': 'test:playlist',
            'extractor_key': 'test:playlist',
            'webpage_url': 'http://example.com',
        }

        def get_downloaded_info_dicts(params):
            ydl = YDL(params)
            # make a deep copy because the dictionary and nested entries
            # can be modified
            ydl.process_ie_result(copy.deepcopy(playlist))
            return ydl.downloaded_info_dicts

        def get_ids(params):
            return [int(v['id']) for v in get_downloaded_info_dicts(params)]

        result = get_ids({})
        self.assertEqual(result, [1, 2, 3, 4])

        result = get_ids({'playlistend': 10})
        self.assertEqual(result, [1, 2, 3, 4])

        result = get_ids({'playlistend': 2})
        self.assertEqual(result, [1, 2])

        result = get_ids({'playliststart': 10})
        self.assertEqual(result, [])

        result = get_ids({'playliststart': 2})
        self.assertEqual(result, [2, 3, 4])

        result = get_ids({'playlist_items': '2-4'})
        self.assertEqual(result, [2, 3, 4])

        result = get_ids({'playlist_items': '2,4'})
        self.assertEqual(result, [2, 4])

        result = get_ids({'playlist_items': '10'})
        self.assertEqual(result, [])

        result = get_ids({'playlist_items': '3-10'})
        self.assertEqual(result, [3, 4])

        result = get_ids({'playlist_items': '2-4,3-4,3'})
        self.assertEqual(result, [2, 3, 4])

        # Tests for https://github.com/ytdl-org/youtube-dl/issues/10591
        # @{
        result = get_downloaded_info_dicts({'playlist_items': '2-4,3-4,3'})
        self.assertEqual(result[0]['playlist_index'], 2)
        self.assertEqual(result[1]['playlist_index'], 3)

        result = get_downloaded_info_dicts({'playlist_items': '2-4,3-4,3'})
        self.assertEqual(result[0]['playlist_index'], 2)
        self.assertEqual(result[1]['playlist_index'], 3)
        self.assertEqual(result[2]['playlist_index'], 4)

        result = get_downloaded_info_dicts({'playlist_items': '4,2'})
        self.assertEqual(result[0]['playlist_index'], 4)
        self.assertEqual(result[1]['playlist_index'], 2)
        # @}

    def test_urlopen_no_file_protocol(self):
        # see https://github.com/ytdl-org/youtube-dl/issues/8227
        ydl = YDL()
        self.assertRaises(compat_urllib_error.URLError, ydl.urlopen, 'file:///etc/passwd')

    def test_do_not_override_ie_key_in_url_transparent(self):
        ydl = YDL()

        class Foo1IE(InfoExtractor):
            _VALID_URL = r'foo1:'

            def _real_extract(self, url):
                return {
                    '_type': 'url_transparent',
                    'url': 'foo2:',
                    'ie_key': 'Foo2',
                    'title': 'foo1 title',
                    'id': 'foo1_id',
                }

        class Foo2IE(InfoExtractor):
            _VALID_URL = r'foo2:'

            def _real_extract(self, url):
                return {
                    '_type': 'url',
                    'url': 'foo3:',
                    'ie_key': 'Foo3',
                }

        class Foo3IE(InfoExtractor):
            _VALID_URL = r'foo3:'

            def _real_extract(self, url):
                return _make_result([{'url': TEST_URL}], title='foo3 title')

        ydl.add_info_extractor(Foo1IE(ydl))
        ydl.add_info_extractor(Foo2IE(ydl))
        ydl.add_info_extractor(Foo3IE(ydl))
        ydl.extract_info('foo1:')
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['url'], TEST_URL)
        self.assertEqual(downloaded['title'], 'foo1 title')
        self.assertEqual(downloaded['id'], 'testid')
        self.assertEqual(downloaded['extractor'], 'testex')
        self.assertEqual(downloaded['extractor_key'], 'TestEx')

    # Test case for https://github.com/ytdl-org/youtube-dl/issues/27064
    def test_ignoreerrors_for_playlist_with_url_transparent_iterable_entries(self):

        ydl = YDL({
            'format': 'extra',
            'ignoreerrors': True,
        })
        ydl.trouble = lambda *_, **__: None

        class VideoIE(InfoExtractor):
            _VALID_URL = r'video:(?P<id>\d+)'

            def _real_extract(self, url):
                video_id = self._match_id(url)
                formats = [{
                    'format_id': 'default',
                    'url': 'url:',
                }]
                if video_id == '0':
                    raise ExtractorError('foo')
                if video_id == '2':
                    formats.append({
                        'format_id': 'extra',
                        'url': TEST_URL,
                    })
                return {
                    'id': video_id,
                    'title': 'Video %s' % video_id,
                    'formats': formats,
                }

        class PlaylistIE(InfoExtractor):
            _VALID_URL = r'playlist:'

            def _entries(self):
                for n in range(3):
                    video_id = compat_str(n)
                    yield {
                        '_type': 'url_transparent',
                        'ie_key': VideoIE.ie_key(),
                        'id': video_id,
                        'url': 'video:%s' % video_id,
                        'title': 'Video Transparent %s' % video_id,
                    }

            def _real_extract(self, url):
                return self.playlist_result(self._entries())

        ydl.add_info_extractor(VideoIE(ydl))
        ydl.add_info_extractor(PlaylistIE(ydl))
        info = ydl.extract_info('playlist:')
        entries = info['entries']
        self.assertEqual(len(entries), 3)
        self.assertTrue(entries[0] is None)
        self.assertTrue(entries[1] is None)
        self.assertEqual(len(ydl.downloaded_info_dicts), 1)
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(entries[2], downloaded)
        self.assertEqual(downloaded['url'], TEST_URL)
        self.assertEqual(downloaded['title'], 'Video Transparent 2')
        self.assertEqual(downloaded['id'], '2')
        self.assertEqual(downloaded['extractor'], 'Video')
        self.assertEqual(downloaded['extractor_key'], 'Video')

    def test_default_times(self):
        """Test addition of missing upload/release/_date from /release_/timestamp"""
        info = {
            'id': '1234',
            'url': TEST_URL,
            'title': 'Title',
            'ext': 'mp4',
            'timestamp': 1631352900,
            'release_timestamp': 1632995931,
        }

        params = {'simulate': True, }
        ydl = FakeYDL(params)
        out_info = ydl.process_ie_result(info)
        self.assertTrue(isinstance(out_info['upload_date'], compat_str))
        self.assertEqual(out_info['upload_date'], '20210911')
        self.assertTrue(isinstance(out_info['release_date'], compat_str))
        self.assertEqual(out_info['release_date'], '20210930')


class TestYoutubeDLCookies(unittest.TestCase):

    @staticmethod
    def encode_cookie(cookie):
        if not isinstance(cookie, dict):
            cookie = vars(cookie)
        for name, value in cookie.items():
            yield name, compat_str(value)

    @classmethod
    def comparable_cookies(cls, cookies):
        # Work around cookiejar cookies not being unicode strings
        return sorted(map(tuple, map(sorted, map(cls.encode_cookie, cookies))))

    def assertSameCookies(self, c1, c2, msg=None):
        return self.assertEqual(
            *map(self.comparable_cookies, (c1, c2)),
            msg=msg)

    def assertSameCookieStrings(self, c1, c2, msg=None):
        return self.assertSameCookies(
            *map(lambda c: compat_http_cookies_SimpleCookie(c).values(), (c1, c2)),
            msg=msg)

    def test_header_cookies(self):

        ydl = FakeYDL()
        ydl.report_warning = lambda *_, **__: None

        def cookie(name, value, version=None, domain='', path='', secure=False, expires=None):
            return compat_http_cookiejar_Cookie(
                version or 0, name, value, None, False,
                domain, bool(domain), bool(domain), path, bool(path),
                secure, expires, False, None, None, rest={})

        test_url, test_domain = (t % ('yt.dl',) for t in ('https://%s/test', '.%s'))

        def test(encoded_cookies, cookies, headers=False, round_trip=None, error_re=None):
            def _test():
                ydl.cookiejar.clear()
                ydl._load_cookies(encoded_cookies, autoscope=headers)
                if headers:
                    ydl._apply_header_cookies(test_url)
                data = {'url': test_url}
                ydl._calc_headers(data)
                self.assertSameCookies(
                    cookies, ydl.cookiejar,
                    'Extracted cookiejar.Cookie is not the same')
                if not headers:
                    self.assertSameCookieStrings(
                        data.get('cookies'), round_trip or encoded_cookies,
                        msg='Cookie is not the same as round trip')
                ydl.__dict__['_YoutubeDL__header_cookies'] = []

            try:
                _test()
            except AssertionError:
                raise
            except Exception as e:
                if not error_re:
                    raise
                assertRegexpMatches(self, e.args[0], error_re.join(('.*',) * 2))

        test('test=value; Domain=' + test_domain, [cookie('test', 'value', domain=test_domain)])
        test('test=value', [cookie('test', 'value')], error_re='Unscoped cookies are not allowed')
        test('cookie1=value1; Domain={0}; Path=/test; cookie2=value2; Domain={0}; Path=/'.format(test_domain), [
            cookie('cookie1', 'value1', domain=test_domain, path='/test'),
            cookie('cookie2', 'value2', domain=test_domain, path='/')])
        cookie_kw = compat_kwargs(
            {'domain': test_domain, 'path': '/test', 'secure': True, 'expires': '9999999999', })
        test('test=value; Domain={domain}; Path={path}; Secure; Expires={expires}'.format(**cookie_kw), [
            cookie('test', 'value', **cookie_kw)])
        test('test="value; "; path=/test; domain=' + test_domain, [
            cookie('test', 'value; ', domain=test_domain, path='/test')],
            round_trip='test="value\\073 "; Domain={0}; Path=/test'.format(test_domain))
        test('name=; Domain=' + test_domain, [cookie('name', '', domain=test_domain)],
             round_trip='name=""; Domain=' + test_domain)
        test('test=value', [cookie('test', 'value', domain=test_domain)], headers=True)
        test('cookie1=value; Domain={0}; cookie2=value'.format(test_domain), [],
             headers=True, error_re='Invalid syntax')
        ydl.report_warning = ydl.report_error
        test('test=value', [], headers=True, error_re='Passing cookies as a header is a potential security risk')

    def test_infojson_cookies(self):
        TEST_FILE = 'test_infojson_cookies.info.json'
        TEST_URL = 'https://example.com/example.mp4'
        COOKIES = 'a=b; Domain=.example.com; c=d; Domain=.example.com'
        COOKIE_HEADER = {'Cookie': 'a=b; c=d'}

        ydl = FakeYDL()
        ydl.process_info = lambda x: ydl._write_info_json('test', x, TEST_FILE)

        def make_info(info_header_cookies=False, fmts_header_cookies=False, cookies_field=False):
            fmt = {'url': TEST_URL}
            if fmts_header_cookies:
                fmt['http_headers'] = COOKIE_HEADER
            if cookies_field:
                fmt['cookies'] = COOKIES
            return _make_result([fmt], http_headers=COOKIE_HEADER if info_header_cookies else None)

        def test(initial_info, note):

            def failure_msg(why):
                return ' when '.join((why, note))

            result = {}
            result['processed'] = ydl.process_ie_result(initial_info)
            self.assertTrue(ydl.cookiejar.get_cookies_for_url(TEST_URL),
                            msg=failure_msg('No cookies set in cookiejar after initial process'))
            ydl.cookiejar.clear()
            with open(TEST_FILE) as infojson:
                result['loaded'] = ydl.sanitize_info(json.load(infojson), True)
            result['final'] = ydl.process_ie_result(result['loaded'].copy(), download=False)
            self.assertTrue(ydl.cookiejar.get_cookies_for_url(TEST_URL),
                            msg=failure_msg('No cookies set in cookiejar after final process'))
            ydl.cookiejar.clear()
            for key in ('processed', 'loaded', 'final'):
                info = result[key]
                self.assertIsNone(
                    traverse_obj(info, ((None, ('formats', 0)), 'http_headers', 'Cookie'), casesense=False, get_all=False),
                    msg=failure_msg('Cookie header not removed in {0} result'.format(key)))
                self.assertSameCookieStrings(
                    traverse_obj(info, ((None, ('formats', 0)), 'cookies'), get_all=False), COOKIES,
                    msg=failure_msg('No cookies field found in {0} result'.format(key)))

        test({'url': TEST_URL, 'http_headers': COOKIE_HEADER, 'id': '1', 'title': 'x'}, 'no formats field')
        test(make_info(info_header_cookies=True), 'info_dict header cokies')
        test(make_info(fmts_header_cookies=True), 'format header cookies')
        test(make_info(info_header_cookies=True, fmts_header_cookies=True), 'info_dict and format header cookies')
        test(make_info(info_header_cookies=True, fmts_header_cookies=True, cookies_field=True), 'all cookies fields')
        test(make_info(cookies_field=True), 'cookies format field')
        test({'url': TEST_URL, 'cookies': COOKIES, 'id': '1', 'title': 'x'}, 'info_dict cookies field only')

        try_rm(TEST_FILE)

    def test_add_headers_cookie(self):
        def check_for_cookie_header(result):
            return traverse_obj(result, ((None, ('formats', 0)), 'http_headers', 'Cookie'), casesense=False, get_all=False)

        ydl = FakeYDL({'http_headers': {'Cookie': 'a=b'}})
        ydl._apply_header_cookies(_make_result([])['webpage_url'])  # Scope to input webpage URL: .example.com

        fmt = {'url': 'https://example.com/video.mp4'}
        result = ydl.process_ie_result(_make_result([fmt]), download=False)
        self.assertIsNone(check_for_cookie_header(result), msg='http_headers cookies in result info_dict')
        self.assertEqual(result.get('cookies'), 'a=b; Domain=.example.com', msg='No cookies were set in cookies field')
        self.assertIn('a=b', ydl.cookiejar.get_cookie_header(fmt['url']), msg='No cookies were set in cookiejar')

        fmt = {'url': 'https://wrong.com/video.mp4'}
        result = ydl.process_ie_result(_make_result([fmt]), download=False)
        self.assertIsNone(check_for_cookie_header(result), msg='http_headers cookies for wrong domain')
        self.assertFalse(result.get('cookies'), msg='Cookies set in cookies field for wrong domain')
        self.assertFalse(ydl.cookiejar.get_cookie_header(fmt['url']), msg='Cookies set in cookiejar for wrong domain')


if __name__ == '__main__':
    unittest.main()
