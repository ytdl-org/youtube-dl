# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import ExtractorError

import json
import math
import random
import re


class AniGamerIE(InfoExtractor):
    _VALID_URL = r'https?://ani\.gamer\.com\.tw/animeVideo\.php\?sn=(?P<id>[0-9]+)'

    _ANI_BASE = 'https://ani.gamer.com.tw'
    _I2_BASE = 'https://i2.bahamut.com.tw'

    _TEST = {
        'url': 'https://yourextractor.com/watch/42',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '42',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        info = {'id': video_id}

        str_info = self._html_search_regex(r'<script[^>]+type="application/ld\+json"[^>]*>(?P<code>[^<]+)', webpage, 'code')
        video_info = json.loads(str_info)

        info['description'] = video_info[2].get('description')
        info['title'] = video_info[2].get('name')
        info['interaction_count'] = video_info[2].get('interactionCount')
        info['thumbnail'] = video_info[2].get('thumbnailUrl')

        if video_info[2].get('uploadDate'):
            dmoj = re.search(r'(?P<y>[0-9]+)-(?P<m>[0-9]+)-(?P<d>[0-9]+)T', video_info[2]['uploadDate'])
            info['upload_date'] = dmoj.group('y') + dmoj.group('m') + dmoj.group('d')

        device_id_json = self._download_json('%s/ajax/getdeviceid.php' % self._ANI_BASE, video_id,
                                        note='Getting device id', query={'id': ''})

        if device_id_json.get('deviceid'):
            device_id = device_id_json.get('deviceid')
        else:
            self.report_warning('Warning! Cannot get device id', video_id)

        ad_js = self._download_webpage('%s/JS/ad/animeVideo2.js' % self._I2_BASE, video_id, )

        minor_code = self._search_regex(r'var\s+getMinorAd\s*=\s*function\(\)\s*\{(?P<code>[^}]+)\};', ad_js, 'code')

        ad_list_s = self._search_regex(r'var\s+adlist\s*=\s*(?P<list>\[(.+?)\]);', minor_code, 'list')
        ad_list = json.loads(ad_list_s)
        del minor_code
        del ad_list_s

        ik = math.floor(9 * random.random())

        ad_sid = ad_list[ik][2]
        ad_query = {
            's': ad_sid,
            'sn': video_id
        }
        self._download_webpage('%s/ajax/videoCastcishu.php' % self._ANI_BASE, video_id,
                                note='Skipping ad', query=ad_query)

        ad_query['ad'] = 'end'
        self._download_webpage('%s/ajax/videoCastcishu.php' % self._ANI_BASE, video_id, note='Skipping ad', query=ad_query)

        m3u8_query = {
            'sn': video_id,
            'device': device_id
        }

        m3u8_json = self._download_json('%s/ajax/m3u8.php' % self._ANI_BASE, video_id, query=m3u8_query)

        if 'error' in m3u8_json:
            raise ExtractorError('Cannot extract URL.')

        index_m3u8_url = m3u8_json.get('src')

        if index_m3u8_url[0:2] == '//':
            index_m3u8_url = 'https:' + index_m3u8_url

        formats = self._extract_m3u8_formats(index_m3u8_url, video_id, ext='mp4', entry_protocol='m3u8_native')

        info['formats'] = formats

        return info