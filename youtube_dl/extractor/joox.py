# coding: utf-8
from __future__ import unicode_literals

import re
import time

from .common import InfoExtractor
import base64


from ..compat import (
    compat_urllib_parse_urlencode,
)


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
        _VALID_URL = r'https?://www\.joox\.com/(?P<country>[a-z]*)/(?P<language>[a-z]*_?[a-z]*)/single/(?P<id>[a-zA-z0-9+]*==)'
        song_id = self._match_id(url)
        p = re.compile(_VALID_URL)
        m = p.search(url)
        _country = m.group('country')
        _lang = m.group('language')
        _code = int(time.time() * 1000)

        query = {
            'songid': song_id,
            'lang': _lang,
            'country': _country,
            'form_type': -1,
            'channel_id': -1,
            '_': _code
        }

        detail_info_page = self._download_webpage(
            "http://api.joox.com/web-fcgi-bin/web_get_songinfo?" + compat_urllib_parse_urlencode(query), song_id)
        detail_info_page = detail_info_page[18:-1]
        song_json = self._parse_json(detail_info_page, song_id)
        song320mp3 = song_json.get('r320Url')
        song192mp3 = song_json.get('r192Url')
        songmp3 = song_json.get('mp3Url')
        songm4a = song_json.get('m4aUrl')
        song_title = song_json.get('msong')
        _duration = song_json.get('minterval')
        album_thumbnail = song_json.get('album_url')
        size128 = song_json.get('size128')
        size320 = song_json.get('size320')
        singer = song_json.get('singer_list')
        singer = singer[0].get('name')
        singer = base64.b64decode(singer).decode('UTF-8')
        publish_time = song_json.get('public_time')
        publish_time = publish_time.replace('-', '')
        formats = []
        _FORMATS = {
            '128m4a': {'url': song192mp3, 'abr': 128},
            'm4a': {'url': songm4a},
            'mp3': {'url': songmp3, 'abr': 128, 'filesize': size128},
            '320mp3': {'url': song320mp3, 'preference': -1, 'abr': 320, 'filesize': size320},
        }
        for format_id, details in _FORMATS.items():
            formats.append({
                'url': details['url'],
                'format': format_id,
                'format_id': format_id,
                'preference': details.get('preference'),
                'abr': details.get('abr'),
                'filesize': details.get('filesize'),
                'resolution': 'audio only'
            })
        return {
            'id': song_id,
            'title': song_title,
            'formats': formats,
            'thumbnail': album_thumbnail,
            'release_date': publish_time,
            'duration': _duration,
            'creator': singer,
        }
