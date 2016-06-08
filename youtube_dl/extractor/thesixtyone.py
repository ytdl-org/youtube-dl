# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import unified_strdate


class TheSixtyOneIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://(?:www\.)?thesixtyone\.com/
        (?:.*?/)*
        (?:
            s|
            song/comments/list|
            song
        )/(?:[^/]+/)?(?P<id>[A-Za-z0-9]+)/?$'''
    _SONG_URL_TEMPLATE = 'http://thesixtyone.com/s/{0:}'
    _SONG_FILE_URL_TEMPLATE = 'http://{audio_server:}/thesixtyone_production/audio/{0:}_stream'
    _THUMBNAIL_URL_TEMPLATE = '{photo_base_url:}_desktop'
    _TESTS = [
        {
            'url': 'http://www.thesixtyone.com/s/SrE3zD7s1jt/',
            'md5': '821cc43b0530d3222e3e2b70bb4622ea',
            'info_dict': {
                'id': 'SrE3zD7s1jt',
                'ext': 'mp3',
                'title': 'CASIO - Unicorn War Mixtape',
                'thumbnail': 're:^https?://.*_desktop$',
                'upload_date': '20071217',
                'duration': 3208,
            }
        },
        {
            'url': 'http://www.thesixtyone.com/song/comments/list/SrE3zD7s1jt',
            'only_matching': True,
        },
        {
            'url': 'http://www.thesixtyone.com/s/ULoiyjuJWli#/s/SrE3zD7s1jt/',
            'only_matching': True,
        },
        {
            'url': 'http://www.thesixtyone.com/#/s/SrE3zD7s1jt/',
            'only_matching': True,
        },
        {
            'url': 'http://www.thesixtyone.com/song/SrE3zD7s1jt/',
            'only_matching': True,
        },
        {
            'url': 'http://www.thesixtyone.com/maryatmidnight/song/StrawberriesandCream/yvWtLp0c4GQ/',
            'only_matching': True,
        },
    ]

    _DECODE_MAP = {
        'x': 'a',
        'm': 'b',
        'w': 'c',
        'q': 'd',
        'n': 'e',
        'p': 'f',
        'a': '0',
        'h': '1',
        'e': '2',
        'u': '3',
        's': '4',
        'i': '5',
        'o': '6',
        'y': '7',
        'r': '8',
        'c': '9'
    }

    def _real_extract(self, url):
        song_id = self._match_id(url)

        webpage = self._download_webpage(
            self._SONG_URL_TEMPLATE.format(song_id), song_id)

        song_data = self._parse_json(self._search_regex(
            r'"%s":\s(\{.*?\})' % song_id, webpage, 'song_data'), song_id)

        if self._search_regex(r'(t61\.s3_audio_load\s*=\s*1\.0;)', webpage, 's3_audio_load marker', default=None):
            song_data['audio_server'] = 's3.amazonaws.com'
        else:
            song_data['audio_server'] = song_data['audio_server'] + '.thesixtyone.com'

        keys = [self._DECODE_MAP.get(s, s) for s in song_data['key']]
        url = self._SONG_FILE_URL_TEMPLATE.format(
            "".join(reversed(keys)), **song_data)

        formats = [{
            'format_id': 'sd',
            'url': url,
            'ext': 'mp3',
        }]

        return {
            'id': song_id,
            'title': '{artist:} - {name:}'.format(**song_data),
            'formats': formats,
            'comment_count': song_data.get('comments_count'),
            'duration': song_data.get('play_time'),
            'like_count': song_data.get('score'),
            'thumbnail': self._THUMBNAIL_URL_TEMPLATE.format(**song_data),
            'upload_date': unified_strdate(song_data.get('publish_date')),
        }
