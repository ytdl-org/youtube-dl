# coding: utf-8
from __future__ import unicode_literals

import random
import string

from .common import InfoExtractor


def to_ascii_hex(str1):
    return ''.join([format(ord(c), 'x') for c in str1])


def generate_random_string(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


class StreamsbIE(InfoExtractor):
    domain = 'viewsb.com'
    _VALID_URL = r'https://' + domain + '/(?P<id>.+)'
    _TEST = {
        'url': 'https://viewsb.com/dxfvlu4qanjx',
        'md5': '488d111a63415369bf90ea83adc8a325',
        'info_dict': {
            'id': 'dxfvlu4qanjx',
            'ext': 'mp4',
            'title': 'Sintel'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        iframe_url = self._search_regex(r'IFRAME SRC=\"(.*)\"', webpage, 'iframe')
        video_code = self._search_regex(r"(\w*).html", iframe_url, 'video_code')

        length = 12
        req = generate_random_string(length) + '||' + video_code + '||' + generate_random_string(length) + '||streamsb'
        ereq = 'https://' + self.domain + '/sources50/' + to_ascii_hex(req)

        video_data = self._download_webpage(ereq, video_id, headers={
            'Referer': iframe_url,
            'watchsb': 'sbstream'}
        )
        player_data = self._parse_json(video_data, video_id)
        formats = self._extract_m3u8_formats(player_data['stream_data']['file'], video_id, ext='mp4', entry_protocol='m3u8_native', m3u8_id='hls', fatal=False)
        return {
            'id': video_id,
            'formats': formats,
            'title': player_data['stream_data']['title']
        }
