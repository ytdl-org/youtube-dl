from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor


class NewgroundsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?newgrounds\.com/(?:audio/listen|portal/view)/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.newgrounds.com/audio/listen/549479',
        'md5': 'fe6033d297591288fa1c1f780386f07a',
        'info_dict': {
            'id': '549479',
            'ext': 'mp3',
            'title': 'B7 - BusMode',
            'uploader': 'Burn7',
        }
    }, {
        'url': 'http://www.newgrounds.com/portal/view/673111',
        'md5': '3394735822aab2478c31b1004fe5e5bc',
        'info_dict': {
            'id': '673111',
            'ext': 'mp4',
            'title': 'Dancin',
            'uploader': 'Squirrelman82',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        music_id = mobj.group('id')
        webpage = self._download_webpage(url, music_id)

        title = self._html_search_regex(
            r'<title>([^>]+)</title>', webpage, 'title')

        uploader = self._html_search_regex(
            [r',"artist":"([^"]+)",', r'[\'"]owner[\'"]\s*:\s*[\'"]([^\'"]+)[\'"],'],
            webpage, 'uploader')

        music_url_json_string = self._html_search_regex(
            r'({"url":"[^"]+"),', webpage, 'music url') + '}'
        music_url_json = json.loads(music_url_json_string)
        music_url = music_url_json['url']

        return {
            'id': music_id,
            'title': title,
            'url': music_url,
            'uploader': uploader,
        }
