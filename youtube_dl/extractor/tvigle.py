# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    str_to_int,
)


class TvigleIE(InfoExtractor):
    IE_NAME = 'tvigle'
    IE_DESC = 'Интернет-телевидение Tvigle.ru'
    _VALID_URL = r'http://(?:www\.)?tvigle\.ru/(?:[^/]+/)+(?P<display_id>[^/]+)/$'

    _TESTS = [
        {
            'url': 'http://www.tvigle.ru/video/brat/',
            'md5': 'ff4344a4894b0524441fb6f8218dc716',
            'info_dict': {
                'id': '5118490',
                'display_id': 'brat',
                'ext': 'mp4',
                'title': 'Брат',
                'description': 'md5:d16ac7c0b47052ea51fddb92c4e413eb',
                'duration': 5722.6,
                'age_limit': 16,
            },
        },
        {
            'url': 'http://www.tvigle.ru/video/vladimir-vysotskii/vedushchii-teleprogrammy-60-minut-ssha-o-vladimire-vysotskom/',
            'md5': 'd9012d7c7c598fe7a11d7fb46dc1f574',
            'info_dict': {
                'id': '5142516',
                'ext': 'mp4',
                'title': 'Ведущий телепрограммы «60 минут» (США) о Владимире Высоцком',
                'description': 'md5:027f7dc872948f14c96d19b4178428a4',
                'duration': 186.080,
                'age_limit': 0,
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        video_id = self._html_search_regex(
            r'<li class="video-preview current_playing" id="(\d+)">', webpage, 'video id')

        video_data = self._download_json(
            'http://cloud.tvigle.ru/api/play/video/%s/' % video_id, display_id)

        item = video_data['playlist']['items'][0]

        title = item['title']
        description = item['description']
        thumbnail = item['thumbnail']
        duration = float_or_none(item['durationMilliseconds'], 1000)
        age_limit = str_to_int(item['ageRestrictions'])

        formats = []
        for vcodec, fmts in item['videos'].items():
            for quality, video_url in fmts.items():
                formats.append({
                    'url': video_url,
                    'format_id': '%s-%s' % (vcodec, quality),
                    'vcodec': vcodec,
                    'height': int(quality[:-1]),
                    'filesize': item['video_files_size'][vcodec][quality],
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': age_limit,
            'formats': formats,
        }