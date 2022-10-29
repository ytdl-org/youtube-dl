# coding: utf-8
from __future__ import unicode_literals

import base64
import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    unified_timestamp,
)


class VXXXIE(InfoExtractor):
    _VALID_URL = r'https?://vxxx\.com/video-(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://vxxx.com/video-80747/',
        'md5': '2f4bfd829b682ff9e3da1bda71b81b81',
        'info_dict': {
            'id': '80747',
            'ext': 'mp4',
            'title': 'Monica Aka Selina',
            'display_id': 'monica-aka-selina',
            'thumbnail': 'https://tn.vxxx.com/contents/videos_screenshots/80000/80747/420x236/1.jpg',
            'description': '',
            'timestamp': 1607167706,
            'upload_date': '20201205',
            'duration': 2373.0,
            'categories': ['Anal', 'Asian', 'BDSM', 'Brunette', 'Toys',
                           'Fetish', 'HD', 'Interracial', 'MILF'],
            'age_limit': 18,
        }
    }]

    def _download_info_object(self, video_id):
        return self._download_json(
            self._INFO_OBJECT_URL_TMPL.format(
                self._BASE_URL,
                int(video_id) // 1000 * 1000,
                video_id,
            ), video_id, headers={'Referer': self._BASE_URL})['video']

    def _download_format_object(self, video_id):
        return self._download_json(
            self._FORMAT_OBJECT_URL_TMPL.format(self._BASE_URL, video_id),
            video_id,
            headers={'Referer': self._BASE_URL}
        )

    @classmethod
    def _get_video_host(cls):
        # or use the proper Python URL parsing functions
        return cls._BASE_URL.split('//')[-1]

    def _decode_base164(self, e):
        """
        Some non-standard encoding called "base164" in the JavaScript code. It's
        similar to the regular base64 with a slightly different alphabet:
            - "АВСЕМ" are Cyrillic letters instead of uppercase Latin letters
            - "." is used instead of "+"; "," is used instead of "/"
            - "~" is used for padding instead of "="
        """

            # using the kwarg to memoise the result
            def get_trans_tbl(from_, to, tbl={}):
                k = (from_, to)
                if not tbl.get(k):
                    tbl[k] = string.maketrans(from_, to)
                return tbl[k]

           # maybe for the 2nd arg:
           # import unicodedata and
           # ''.join((unicodedata.lookup('CYRILLIC CAPITAL LETTER ' + x) for x in ('A', 'BE', 'ES', 'IE', 'EM'))) + '+/='
           trans_tbl = get_trans_tbl('АBCEM.,~', 'ABCEM+/=')
           return base64.b64decode(e.translate(trans_tbl)
                                ).decode()

    def _extract_info(self, url):
        video_id = self._match_id(url)

        info_object = self._download_info_object(video_id)

        title = info_object['title']
        stats = info_object.get('statistics') or {}
        info = {
            'id': video_id,
            'title': title,
            'display_id': info_object.get('dir'),
            'thumbnail': url_or_none(info_object.get('thumb')),
            'description': strip_or_none(info_object('description')) or None,
            'timestamp': unified_timestamp(info_object.get('post_date')),
            'duration': parse_duration(info_object.get('duration')),
            'view_count': int_or_none(stats.get('viewed')),
            'like_count': int_or_none(stats.get('likes')),
            'dislike_count': int_or_none(stats.get('dislikes')),
            'average_rating': float_or_none(stats.get('rating')),
            'categories': [category['title'] for category in (info_object.get('categories') or {}).values() if category.get('title')],
            'age_limit': 18,
        }

        format_object = self._download_format_object(video_id)
        m3u8_formats = self._extract_m3u8_formats(
            'https://{0}{1}&f=video.m3u8'.format(
                self._get_video_host(),
                self._decode_base164(format_object[0]['video_url'])
            ),
            video_id, 'mp4')
        self._sort_formats(m3u8_formats)
        info['formats'] = m3u8_formats

        return info

    def _real_extract(self, url):
        info = self._extract_info(url)

        if not info['formats']:
            return self.url_result(url, 'Generic')

        return info
