# coding: utf-8
from __future__ import unicode_literals

import re
import time

from .common import InfoExtractor
import base64


from ..compat import (
    compat_urllib_parse_urlencode,
)

from ..utils import ExtractorError


class JooxIE(InfoExtractor):
    IE_NAME = 'jooxmusic:single'
    IE_DESC = 'Joox'
    _VALID_URL = r'https?://www\.joox\.com/(?P<country>[a-z]*)/(?P<language>[a-z]*_?[a-z]*)/single/(?P<id>[a-zA-z0-9+]*==)'
    _TESTS = [{
        'url': 'http://www.joox.com/hk/zh_hk/single/WYL92NDGHMhCs3GdDZBsMQ==',
        'md5': '81a3d00b7422edb16a59ee9fe3dcb5dd',
        'info_dict': {
            'id': 'WYL92NDGHMhCs3GdDZBsMQ==',
            'ext': 'mp3',
            'title': '忍',
            'release_date': '20180214',
            'creator': '林欣彤',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }]

    def _real_extract(self, url):
        song_id = self._match_id(url)
        p = re.compile(self._VALID_URL)
        m = p.search(url)
        _country = m.group('country')
        _lang = m.group('language')
        _code = int(time.time() * 1000)

        parameter = {
            'songid': song_id,
            'lang': _lang,
            'country': _country,
            'form_type': -1,
            'channel_id': -1,
            '_': _code
        }

        detail_info_page = self._download_webpage(
            "http://api.joox.com/web-fcgi-bin/web_get_songinfo?" + compat_urllib_parse_urlencode(parameter), song_id)
        detail_info_page = detail_info_page[18:-1]
        song_json = self._parse_json(detail_info_page, song_id)
        if song_json.get('code') != 0:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, "invalid songid"), expected=True)

        song320mp3 = song_json.get('r320Url')
        song192mp3 = song_json.get('r192Url')
        songmp3 = song_json.get('mp3Url')
        songm4a = song_json.get('m4aUrl')
        song_title = song_json.get('msong')
        duration = song_json.get('minterval')
        album_thumbnail = song_json.get('album_url')
        size128 = song_json.get('size128')
        size320 = song_json.get('size320')
        singer = song_json.get('singer_list')
        singer = singer[0].get('name')
        singer = base64.b64decode(singer).decode('UTF-8')
        publish_time = song_json.get('public_time')
        publish_time = publish_time.replace('-', '')
        formats = []
        formats.extend([
            {'url': song192mp3, 'format_id': '128m4a', 'abr': 128, },
            {'url': songm4a, 'format_id': 'm4a', },
            {'url': songmp3, 'format_id': 'mp3', 'abr': 128, 'filesize': int(size128)},
            {'url': song320mp3, 'format_id': '320mp3', 'abr': 320, 'preference': -1, 'filesize': int(size320), }
        ])
        formats = [x for x in formats if x['url'] != '']

        return {
            'id': song_id,
            'title': song_title,
            'formats': formats,
            'thumbnail': album_thumbnail,
            'release_date': publish_time,
            'duration': int(duration),
            'artist': singer,
        }
