# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    xpath_text,
    int_or_none,
)


class WallaIE(InfoExtractor):
    _VALID_URL = r'http://[^\.]+\.walla\.co\.il/[^/]+/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://news.walla.co.il/item/2835878',
        'info_dict': {
            'id': '2663876',
            'ext': 'mp4',
            'title': 'בנט יורה: "בפעם הבאה יהיה רב ראשי אחד לישראל"',
            'description': 'md5:5f3ac43a8abc132ccaa1a6894a137440',
            'thumbnail': 're:^https?://.*\.jpg',
            'duration': 112,
        },
        'params': {
            # stream download
            'skip_download': True,
        }
    }, {
        'url': 'http://vod.walla.co.il/movie/2642630/one-direction-all-for-one',
        'info_dict': {
            'id': '2642630',
            'ext': 'mp4',
            'title': 'וואן דיירקשן: ההיסטריה',
            'description': 'md5:de9e2512a92442574cdb0913c49bc4d8',
            'thumbnail': 're:^https?://.*\.jpg',
            'duration': 3600,
        },
        'params': {
            # stream download
            'skip_download': True,
        }
    }]

    _SUBTITLE_LANGS = {
        'עברית': 'heb',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        video = self._download_xml(
            'http://video.walla.co.il/?w=//%s/@@/video/flv_pl' % video_id,
            video_id)

        item = video.find('./items/item')

        if item is None:
            raise ExtractorError('The item doesn\'t exist or has no video.', expected=True)

        title = xpath_text(item, './title', 'title')
        description = next(
            item for item in [
                xpath_text(item, './synopsis', 'description'),
                xpath_text(item, './subtitle', 'description'),
                '',
            ] if item is not None
        )
        thumbnail = xpath_text(item, './preview_pic', 'thumbnail')
        duration = int_or_none(xpath_text(item, './duration', 'duration'))
        default_file = xpath_text(item, './src', 'src')

        subtitles = {}
        for subtitle in item.findall('./subtitles/subtitle'):
            lang = xpath_text(subtitle, './title')
            subtitles[self._SUBTITLE_LANGS.get(lang, lang)] = [{
                'ext': 'srt',
                'url': xpath_text(subtitle, './src'),
            }]

        playlist_url = 'http://walla-s.vidnt.com/walla_vod/_definst_/%s.mp4/playlist.m3u8'

        formats = []
        formats.append(
            {
                'url': playlist_url % default_file,
                'ext': 'mp4',
                'format_id': 40,
            }
        )

        for quality in item.findall('./qualities/quality'):
            format_id = xpath_text(quality, './title')
            fmt = {
                'url': playlist_url % xpath_text(quality, './src'),
                'ext': 'mp4',
                'format_id': quality.attrib['type'],
            }
            m = re.search(r'^(?P<height>\d+)[Pp]', format_id)
            if m:
                fmt['height'] = int(m.group('height'))
            formats.append(fmt)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
        }
