# coding: utf-8
from __future__ import unicode_literals

import base64
import re

from .common import InfoExtractor
from ..utils import unified_timestamp, parse_duration


class VXXXIE(InfoExtractor):
    _VALID_URL = r'https?://vxxx\.com/video-(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://vxxx.com/video-80747/',
        'md5': '4736e868b0e008b4ff9dc09585c26c52',
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
            'https://vxxx.com/api/json/video/86400/0/{}/{}.json'.format(
                int(video_id) // 1000 * 1000,
                video_id,
            ), video_id, headers={'Referer': 'https://vxxx.com'})['video']

    def _download_format_object(self, video_id):
        return self._download_json(
            'https://vxxx.com/api/videofile.php?video_id={}'.format(video_id),
            video_id,
            headers={'Referer': 'https://vxxx.com'}
        )

    def _get_video_host(self):
        return 'vxxx.com'

    def _decode_base164(self, e):
        """
        Some non-standard encoding called "base164" in the JavaScript code. It's
        similar to the regular base64 with a slightly different alphabet:
            - "АВСЕМ" are Cyrillic letters instead of uppercase English letters
            - "." is used instead of "+"; "," is used instead of "/"
            - "~" is used for padding instead of "="
        """

        return base64.b64decode(e
                                .replace("А", "A")
                                .replace("В", "B")
                                .replace("С", "C")
                                .replace("Е", "E")
                                .replace("М", "M")
                                .replace(".", "+")
                                .replace(",", "/")
                                .replace("~", "=")
                                ).decode()

    def _extract_info(self, url):
        matches = re.match(self._VALID_URL, url)
        video_id = matches.group('id')

        info_object = self._download_info_object(video_id)

        info = {
            'id': video_id,
            'title': info_object['title'],
            'display_id': info_object['dir'],
            'thumbnail': info_object['thumb'],
            'description': info_object['description'],
            'timestamp': unified_timestamp(info_object['post_date']),
            'duration': parse_duration(info_object['duration']),
            'view_count': int(info_object['statistics']['viewed']),
            'like_count': int(info_object['statistics']['likes']),
            'dislike_count': int(info_object['statistics']['dislikes']),
            'average_rating': float(info_object['statistics']['rating']),
            'categories': [category['title'] for category in info_object['categories'].values()],
            'age_limit': 18,
            'formats': None
        }

        qualities = {
            '_fhd.mp4': -1,  # 1080p
            '_hd.mp4': -2,   # 720p
            '_hq.mp4': -2,   # 720p
            '_sd.mp4': -3,   # 480p
            '_lq.mp4': -3    # 480p
        }

        format_object = self._download_format_object(video_id)
        formats = list(map(lambda f: {
            'url': "https://{}{}".format(
                self._get_video_host(),
                self._decode_base164(f['video_url'])
            ),
            'format_id': f['format'],
            'quality': qualities.get(f['format'], -1)
        }, format_object))
        self._sort_formats(formats)

        info['formats'] = formats
        return info

    def _real_extract(self, url):
        info = self._extract_info(url)

        if not info['formats']:
            return self.url_result(url, 'Generic')

        return info
