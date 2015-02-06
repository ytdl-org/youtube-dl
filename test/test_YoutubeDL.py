#!/usr/bin/env python

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import copy

from test.helper import FakeYDL, assertRegexpMatches
from youtube_dl import YoutubeDL
from youtube_dl.extractor import YoutubeIE
from youtube_dl.postprocessor.common import PostProcessor


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


class TestFormatSelection(unittest.TestCase):
    def test_prefer_free_formats(self):
        # Same resolution => download webm
        ydl = YDL()
        ydl.params['prefer_free_formats'] = True
        formats = [
            {'ext': 'webm', 'height': 460, 'url': 'x'},
            {'ext': 'mp4', 'height': 460, 'url': 'y'},
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
            {'ext': 'webm', 'height': 720, 'url': 'a'},
            {'ext': 'mp4', 'height': 1080, 'url': 'b'},
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
            {'ext': 'webm', 'height': 720, 'url': '_'},
            {'ext': 'mp4', 'height': 720, 'url': '_'},
            {'ext': 'flv', 'height': 720, 'url': '_'},
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
            {'ext': 'flv', 'height': 720, 'url': '_'},
            {'ext': 'webm', 'height': 720, 'url': '_'},
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
        info_dict = _make_result(formats)

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
            {'format_id': '35', 'ext': 'mp4', 'preference': 1, 'url': '_'},
            {'format_id': '45', 'ext': 'webm', 'preference': 2, 'url': '_'},
            {'format_id': '47', 'ext': 'webm', 'preference': 3, 'url': '_'},
            {'format_id': '2', 'ext': 'flv', 'preference': 4, 'url': '_'},
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

    def test_format_selection_audio(self):
        formats = [
            {'format_id': 'audio-low', 'ext': 'webm', 'preference': 1, 'vcodec': 'none', 'url': '_'},
            {'format_id': 'audio-mid', 'ext': 'webm', 'preference': 2, 'vcodec': 'none', 'url': '_'},
            {'format_id': 'audio-high', 'ext': 'flv', 'preference': 3, 'vcodec': 'none', 'url': '_'},
            {'format_id': 'vid', 'ext': 'mp4', 'preference': 4, 'url': '_'},
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
            {'format_id': 'vid-low', 'ext': 'mp4', 'preference': 1, 'url': '_'},
            {'format_id': 'vid-high', 'ext': 'mp4', 'preference': 2, 'url': '_'},
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
            {'format_id': 'dash-video-low', 'ext': 'mp4', 'preference': 1, 'acodec': 'none', 'url': '_'},
            {'format_id': 'dash-video-high', 'ext': 'mp4', 'preference': 2, 'acodec': 'none', 'url': '_'},
            {'format_id': 'vid', 'ext': 'mp4', 'preference': 3, 'url': '_'},
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

    def test_youtube_format_selection(self):
        order = [
            '38', '37', '46', '22', '45', '35', '44', '18', '34', '43', '6', '5', '36', '17', '13',
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

        for f1id, f2id in zip(order, order[1:]):
            f1 = YoutubeIE._formats[f1id].copy()
            f1['format_id'] = f1id
            f1['url'] = 'url:' + f1id
            f2 = YoutubeIE._formats[f2id].copy()
            f2['format_id'] = f2id
            f2['url'] = 'url:' + f2id

            info_dict = _make_result([f1, f2], extractor='youtube')
            ydl = YDL()
            yie = YoutubeIE(ydl)
            yie._sort_formats(info_dict['formats'])
            ydl.process_ie_result(info_dict)
            downloaded = ydl.downloaded_info_dicts[0]
            self.assertEqual(downloaded['format_id'], f1id)

            info_dict = _make_result([f2, f1], extractor='youtube')
            ydl = YDL()
            yie = YoutubeIE(ydl)
            yie._sort_formats(info_dict['formats'])
            ydl.process_ie_result(info_dict)
            downloaded = ydl.downloaded_info_dicts[0]
            self.assertEqual(downloaded['format_id'], f1id)

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

    def test_postprocessors(self):
        filename = 'post-processor-testfile.mp4'
        audiofile = filename + '.mp3'

        class SimplePP(PostProcessor):
            def run(self, info):
                with open(audiofile, 'wt') as f:
                    f.write('EXAMPLE')
                info['filepath']
                return False, info

        def run_pp(params):
            with open(filename, 'wt') as f:
                f.write('EXAMPLE')
            ydl = YoutubeDL(params)
            ydl.add_post_processor(SimplePP())
            ydl.post_process(filename, {'filepath': filename})

        run_pp({'keepvideo': True})
        self.assertTrue(os.path.exists(filename), '%s doesn\'t exist' % filename)
        self.assertTrue(os.path.exists(audiofile), '%s doesn\'t exist' % audiofile)
        os.unlink(filename)
        os.unlink(audiofile)

        run_pp({'keepvideo': False})
        self.assertFalse(os.path.exists(filename), '%s exists' % filename)
        self.assertTrue(os.path.exists(audiofile), '%s doesn\'t exist' % audiofile)
        os.unlink(audiofile)


if __name__ == '__main__':
    unittest.main()
