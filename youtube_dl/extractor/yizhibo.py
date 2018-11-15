# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    js_to_json,
)


class YizhiboIE(InfoExtractor):
    _VALID_URL = r'https?://(?:wb\.)?yizhibo\.com/l/(?P<id>[^/?#&.]+)\.html(?:[?#].*)?'

    _TEST = {
        'url': 'https://wb.yizhibo.com/l/QcnhER5fkh_drtI3.html',
        'md5': '4a61687d770de05fd2b67bd7f1b52bc3',
        'info_dict': {
            'id': 'QcnhER5fkh_drtI3',
            'ext': 'm3u8',
            'title': 'hyominnn00-一直播'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._search_regex(r'<title>(.*?)</title>', webpage, 'video title')

        json_raw = self._search_regex(r'window\.anchor *= *({[\s\S]*?});', webpage, 'video data')
        json = self._parse_json(json_raw, video_id, transform_source=js_to_json)

        play_url = json['play_url']

        formats = self._extract_m3u8_formats(play_url, video_id)

        return {
            'id': video_id,
            'url': url,
            'title': title,
            'formats': formats,
        }
