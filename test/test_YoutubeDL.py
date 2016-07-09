#!/usr/bin/env python

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
import subprocess
import ssl
import threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import copy

from test.helper import FakeYDL, assertRegexpMatches
from youtube_dl import YoutubeDL
<<<<<<< HEAD
from youtube_dl.compat import compat_str
from youtube_dl.compat import compat_http_server, compat_urllib_request
=======
from youtube_dl.compat import compat_str, compat_urllib_error
>>>>>>> upstream/master
from youtube_dl.extractor import YoutubeIE
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.postprocessor.common import PostProcessor
from youtube_dl.utils import ExtractorError, match_filter_func
from youtube_dl.utils import encodeArgument

from test.helper import (
    assertGreaterEqual,
    expect_warnings,
    get_params,
    gettestcases,
    expect_info_dict,
    try_rm,
    report_warning,
)


import hashlib
import io
import json
import socket

import youtube_dl.YoutubeDL
from youtube_dl.compat import (
    compat_http_client,
    compat_urllib_error,
    compat_HTTPError,
)
from youtube_dl.utils import (
    DownloadError,
    ExtractorError,
    format_bytes,
    UnavailableVideoError,
)
from youtube_dl.extractor import get_info_extractor

RETRIES = 3

rootDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    _DEV_NULL = subprocess.DEVNULL
except AttributeError:
    _DEV_NULL = open(os.devnull, 'wb')

TEST_URL = 'http://localhost/sample.mp4'
TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class YoutubeDL(youtube_dl.YoutubeDL):
    def __init__(self, *args, **kwargs):
        self.to_stderr = self.to_screen
        self.processed_info_dicts = []
        super(YoutubeDL, self).__init__(*args, **kwargs)

    def report_warning(self, message):
        # Don't accept warnings during tests
        raise ExtractorError(message)

    def process_info(self, info_dict):
        self.processed_info_dicts.append(info_dict)
        return super(YoutubeDL, self).process_info(info_dict)


def _file_md5(fn):
    with open(fn, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

defs = gettestcases()


class TestDownload(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.defs = defs

class YDL(FakeYDL):
    def __init__(self, *args, **kwargs):
        super(YDL, self).__init__(*args, **kwargs)
        self.downloaded_info_dicts = []
        self.msgs = []

    def process_info(self, info_dict):
        self.downloaded_info_dicts.append(info_dict)

    def to_screen(self, msg):
        self.msgs.append(msg)


def _make_result(formats, **kwargs):
    res = {
        'formats': formats,
        'id': 'testid',
        'title': 'testttitle',
        'extractor': 'testex',
    }
    res.update(**kwargs)
    return res

class HTTPTestRequestHandler(compat_http_server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/video.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<html><video src="/vid.mp4" /></html>')
        elif self.path == '/vid.mp4':
            self.send_response(200)
            self.send_header('Content-Type', 'video/mp4')
            self.end_headers()
            self.wfile.write(b'\x00\x00\x00\x00\x20\x66\x74[video]')
        else:
            assert False


class FakeLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

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

    def test_invalid_format_specs(self):
        def assert_syntax_error(format_spec):
            ydl = YDL({'format': format_spec})
            info_dict = _make_result([{'format_id': 'foo', 'url': TEST_URL}])
            self.assertRaises(SyntaxError, ydl.process_ie_result, info_dict)

        assert_syntax_error('bestvideo,,best')
        assert_syntax_error('+bestaudio')
        assert_syntax_error('bestvideo+')
        assert_syntax_error('/')

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
        }

        def fname(templ):
            ydl = YoutubeDL({'outtmpl': templ})
            return ydl.prepare_filename(info)
        self.assertEqual(fname('%(id)s.%(ext)s'), '1234.mp4')
        self.assertEqual(fname('%(id)s-%(width)s.%(ext)s'), '1234-NA.mp4')
        # Replace missing fields with 'NA'
        self.assertEqual(fname('%(uploader_date)s-%(id)s.%(ext)s'), 'NA-1234.mp4')

    def test_format_note(self):
        ydl = YoutubeDL()
        self.assertEqual(ydl._format_note({}), '')
        assertRegexpMatches(self, ydl._format_note({
            'vbr': 10,
        }), '^\s*10k$')
        assertRegexpMatches(self, ydl._format_note({
            'fps': 30,
        }), '^30fps$')

    def test_postprocessors(self):
        filename = 'post-processor-testfile.mp4'
        audiofile = filename + '.mp3'

        class SimplePP(PostProcessor):
            def run(self, info):
                with open(audiofile, 'wt') as f:
                    f.write('EXAMPLE')
                return [info['filepath']], info

        def run_pp(params, PP):
            with open(filename, 'wt') as f:
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
                with open(info['filepath'], 'wt') as f:
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
        }
        second = {
            'id': '2',
            'url': TEST_URL,
            'title': 'two',
            'extractor': 'TEST',
            'duration': 10,
            'description': 'foo',
            'filesize': 5 * 1024,
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

        def get_ids(params):
            ydl = YDL(params)
            # make a copy because the dictionary can be modified
            ydl.process_ie_result(playlist.copy())
            return [int(v['id']) for v in ydl.downloaded_info_dicts]

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

<<<<<<< HEAD
    def test_import(self):
        subprocess.check_call([sys.executable, '-c', 'import youtube_dl'], cwd=rootDir)

    def test_module_exec(self):
        if sys.version_info >= (2, 7):  # Python 2.6 doesn't support package execution
            subprocess.check_call([sys.executable, '-m', 'youtube_dl', '--version'], cwd=rootDir, stdout=_DEV_NULL)

    def test_main_exec(self):
        subprocess.check_call([sys.executable, 'youtube_dl/__main__.py', '--version'], cwd=rootDir, stdout=_DEV_NULL)

    def test_cmdline_umlauts(self):
        p = subprocess.Popen(
            [sys.executable, 'youtube_dl/__main__.py', encodeArgument('ä'), '--version'],
            cwd=rootDir, stdout=_DEV_NULL, stderr=subprocess.PIPE)
        _, stderr = p.communicate()
        self.assertFalse(stderr)

class TestHTTP(unittest.TestCase):
    def setUp(self):
        certfn = os.path.join(TEST_DIR, 'testcert.pem')
        self.httpd = compat_http_server.HTTPServer(
            ('localhost', 0), HTTPTestRequestHandler)
        self.httpd.socket = ssl.wrap_socket(
            self.httpd.socket, certfile=certfn, server_side=True)
        self.port = self.httpd.socket.getsockname()[1]
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def test_nocheckcertificate(self):
        if sys.version_info >= (2, 7, 9):  # No certificate checking anyways
            ydl = YoutubeDL({'logger': FakeLogger()})
            self.assertRaises(
                Exception,
                ydl.extract_info, 'https://localhost:%d/video.html' % self.port)

        ydl = YoutubeDL({'logger': FakeLogger(), 'nocheckcertificate': True})
        r = ydl.extract_info('https://localhost:%d/video.html' % self.port)
        self.assertEqual(r['url'], 'https://localhost:%d/vid.mp4' % self.port)


def _build_proxy_handler(name):
    class HTTPTestRequestHandler(compat_http_server.BaseHTTPRequestHandler):
        proxy_name = name

        def log_message(self, format, *args):
            pass

        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write('{self.proxy_name}: {self.path}'.format(self=self).encode('utf-8'))
    return HTTPTestRequestHandler


class TestProxy(unittest.TestCase):
    def setUp(self):
        self.proxy = compat_http_server.HTTPServer(
            ('localhost', 0), _build_proxy_handler('normal'))
        self.port = self.proxy.socket.getsockname()[1]
        self.proxy_thread = threading.Thread(target=self.proxy.serve_forever)
        self.proxy_thread.daemon = True
        self.proxy_thread.start()

        self.cn_proxy = compat_http_server.HTTPServer(
            ('localhost', 0), _build_proxy_handler('cn'))
        self.cn_port = self.cn_proxy.socket.getsockname()[1]
        self.cn_proxy_thread = threading.Thread(target=self.cn_proxy.serve_forever)
        self.cn_proxy_thread.daemon = True
        self.cn_proxy_thread.start()

    def test_proxy(self):
        cn_proxy = 'localhost:{0}'.format(self.cn_port)
        ydl = YoutubeDL({
            'proxy': 'localhost:{0}'.format(self.port),
            'cn_verification_proxy': cn_proxy,
        })
        url = 'http://foo.com/bar'
        response = ydl.urlopen(url).read().decode('utf-8')
        self.assertEqual(response, 'normal: {0}'.format(url))

        req = compat_urllib_request.Request(url)
        req.add_header('Ytdl-request-proxy', cn_proxy)
        response = ydl.urlopen(req).read().decode('utf-8')
        self.assertEqual(response, 'cn: {0}'.format(url))

def generator(test_case):

    def test_template(self):
        ie = youtube_dl.extractor.get_info_extractor(test_case['name'])
        other_ies = [get_info_extractor(ie_key) for ie_key in test_case.get('add_ie', [])]
        is_playlist = any(k.startswith('playlist') for k in test_case)
        test_cases = test_case.get(
            'playlist', [] if is_playlist else [test_case])

        def print_skipping(reason):
            print('Skipping %s: %s' % (test_case['name'], reason))
        if not ie.working():
            print_skipping('IE marked as not _WORKING')
            return

        for tc in test_cases:
            info_dict = tc.get('info_dict', {})
            if not (info_dict.get('id') and info_dict.get('ext')):
                raise Exception('Test definition incorrect. The output file cannot be known. Are both \'id\' and \'ext\' keys present?')

        if 'skip' in test_case:
            print_skipping(test_case['skip'])
            return
        for other_ie in other_ies:
            if not other_ie.working():
                print_skipping('test depends on %sIE, marked as not WORKING' % other_ie.ie_key())
                return

        params = get_params(test_case.get('params', {}))
        if is_playlist and 'playlist' not in test_case:
            params.setdefault('extract_flat', 'in_playlist')
            params.setdefault('skip_download', True)

        ydl = YoutubeDL(params, auto_init=False)
        ydl.add_default_info_extractors()
        finished_hook_called = set()

        def _hook(status):
            if status['status'] == 'finished':
                finished_hook_called.add(status['filename'])
        ydl.add_progress_hook(_hook)
        expect_warnings(ydl, test_case.get('expected_warnings', []))

        def get_tc_filename(tc):
            return ydl.prepare_filename(tc.get('info_dict', {}))

        res_dict = None

        def try_rm_tcs_files(tcs=None):
            if tcs is None:
                tcs = test_cases
            for tc in tcs:
                tc_filename = get_tc_filename(tc)
                try_rm(tc_filename)
                try_rm(tc_filename + '.part')
                try_rm(os.path.splitext(tc_filename)[0] + '.info.json')
        try_rm_tcs_files()
        try:
            try_num = 1
            while True:
                try:
                    # We're not using .download here sine that is just a shim
                    # for outside error handling, and returns the exit code
                    # instead of the result dict.
                    res_dict = ydl.extract_info(
                        test_case['url'],
                        force_generic_extractor=params.get('force_generic_extractor', False))
                except (DownloadError, ExtractorError) as err:
                    # Check if the exception is not a network related one
                    if not err.exc_info[0] in (compat_urllib_error.URLError, socket.timeout, UnavailableVideoError, compat_http_client.BadStatusLine) or (err.exc_info[0] == compat_HTTPError and err.exc_info[1].code == 503):
                        raise

                    if try_num == RETRIES:
                        report_warning('Failed due to network errors, skipping...')
                        return

                    print('Retrying: {0} failed tries\n\n##########\n\n'.format(try_num))

                    try_num += 1
                else:
                    break

            if is_playlist:
                self.assertTrue(res_dict['_type'] in ['playlist', 'multi_video'])
                self.assertTrue('entries' in res_dict)
                expect_info_dict(self, res_dict, test_case.get('info_dict', {}))

            if 'playlist_mincount' in test_case:
                assertGreaterEqual(
                    self,
                    len(res_dict['entries']),
                    test_case['playlist_mincount'],
                    'Expected at least %d in playlist %s, but got only %d' % (
                        test_case['playlist_mincount'], test_case['url'],
                        len(res_dict['entries'])))
            if 'playlist_count' in test_case:
                self.assertEqual(
                    len(res_dict['entries']),
                    test_case['playlist_count'],
                    'Expected %d entries in playlist %s, but got %d.' % (
                        test_case['playlist_count'],
                        test_case['url'],
                        len(res_dict['entries']),
                    ))
            if 'playlist_duration_sum' in test_case:
                got_duration = sum(e['duration'] for e in res_dict['entries'])
                self.assertEqual(
                    test_case['playlist_duration_sum'], got_duration)

            for tc in test_cases:
                tc_filename = get_tc_filename(tc)
                if not test_case.get('params', {}).get('skip_download', False):
                    self.assertTrue(os.path.exists(tc_filename), msg='Missing file ' + tc_filename)
                    self.assertTrue(tc_filename in finished_hook_called)
                    expected_minsize = tc.get('file_minsize', 10000)
                    if expected_minsize is not None:
                        if params.get('test'):
                            expected_minsize = max(expected_minsize, 10000)
                        got_fsize = os.path.getsize(tc_filename)
                        assertGreaterEqual(
                            self, got_fsize, expected_minsize,
                            'Expected %s to be at least %s, but it\'s only %s ' %
                            (tc_filename, format_bytes(expected_minsize),
                                format_bytes(got_fsize)))
                    if 'md5' in tc:
                        md5_for_file = _file_md5(tc_filename)
                        self.assertEqual(md5_for_file, tc['md5'])
                info_json_fn = os.path.splitext(tc_filename)[0] + '.info.json'
                self.assertTrue(
                    os.path.exists(info_json_fn),
                    'Missing info file %s' % info_json_fn)
                with io.open(info_json_fn, encoding='utf-8') as infof:
                    info_dict = json.load(infof)

                expect_info_dict(self, info_dict, tc.get('info_dict', {}))
        finally:
            try_rm_tcs_files()
            if is_playlist and res_dict is not None and res_dict.get('entries'):
                # Remove all other files that may have been extracted if the
                # extractor returns full results even with extract_flat
                res_tcs = [{'info_dict': e} for e in res_dict['entries']]
                try_rm_tcs_files(res_tcs)

    return test_template

# And add them to TestDownload
for n, test_case in enumerate(defs):
    test_method = generator(test_case)
    tname = 'test_' + str(test_case['name'])
    i = 1
    while hasattr(TestDownload, tname):
        tname = 'test_%s_%d' % (test_case['name'], i)
        i += 1
    test_method.__name__ = str(tname)
    setattr(TestDownload, test_method.__name__, test_method)
    del test_method
=======
    def test_urlopen_no_file_protocol(self):
        # see https://github.com/rg3/youtube-dl/issues/8227
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
                return _make_result([{'url': TEST_URL}])

        ydl.add_info_extractor(Foo1IE(ydl))
        ydl.add_info_extractor(Foo2IE(ydl))
        ydl.add_info_extractor(Foo3IE(ydl))
        ydl.extract_info('foo1:')
        downloaded = ydl.downloaded_info_dicts[0]
        self.assertEqual(downloaded['url'], TEST_URL)

>>>>>>> upstream/master

if __name__ == '__main__':
    unittest.main()
