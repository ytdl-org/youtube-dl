# coding: utf-8
from __future__ import unicode_literals

import binascii
import random
import re
import string

from .common import InfoExtractor
from ..utils import urljoin, url_basename


def to_ascii_hex(str1):
    return binascii.hexlify(str1.encode('utf-8')).decode('ascii')


def generate_random_string(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


class StreamsbIE(InfoExtractor):
    _DOMAINS = ('viewsb.com', )
    _VALID_URL = r'https://(?P<domain>%s)/(?P<id>.+)' % '|'.join(_DOMAINS)
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
        domain, video_id = re.match(self._VALID_URL, url).group('domain', 'id')
        webpage = self._download_webpage(url, video_id)

        iframe_rel_url = self._search_regex(r'''(?i)<iframe\b[^>]+\bsrc\s*=\s*('|")(?P<path>/.*\.html)\1''', webpage, 'iframe', group='path')
        iframe_url = urljoin('https://' + domain, iframe_rel_url)

        iframe_data = self._download_webpage(iframe_url, video_id)
        app_version = self._search_regex(r'''<script\b[^>]+\bsrc\s*=\s*["|'].*/app\.min\.(\d+)\.js''', iframe_data, 'app version', fatal=False) or '50'

        video_code = url_basename(iframe_url).rsplit('.')[0]

        length = 12
        req = '||'.join((generate_random_string(length), video_code, generate_random_string(length), 'streamsb'))
        ereq = 'https://{0}/sources{1}/{2}'.format(domain, app_version, to_ascii_hex(req))

        video_data = self._download_webpage(ereq, video_id, headers={
            'Referer': iframe_url,
            'watchsb': 'sbstream',
        })
        player_data = self._parse_json(video_data, video_id)
        title = player_data['stream_data']['title']
        formats = self._extract_m3u8_formats(player_data['stream_data']['file'], video_id, ext='mp4', entry_protocol='m3u8_native', m3u8_id='hls', fatal=False)
        return {
            'id': video_id,
            'formats': formats,
            'title': title,
        }
