# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    parse_age_limit,
)


class TvigleIE(InfoExtractor):
    IE_NAME = 'tvigle'
    IE_DESC = 'Интернет-телевидение Tvigle.ru'
    _VALID_URL = r'http://(?:www\.)?tvigle\.ru/(?:[^/]+/)+(?P<id>[^/]+)/$'

    _TESTS = [
        {
            'url': 'http://www.tvigle.ru/video/sokrat/',
            'md5': '36514aed3657d4f70b4b2cef8eb520cd',
            'info_dict': {
                'id': '1848932',
                'display_id': 'sokrat',
                'ext': 'flv',
                'title': 'Сократ',
                'description': 'md5:a05bd01be310074d5833efc6743be95e',
                'duration': 6586,
                'age_limit': 0,
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
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_id = self._html_search_regex(
            r'<li class="video-preview current_playing" id="(\d+)">', webpage, 'video id')

        video_data = self._download_json(
            'http://cloud.tvigle.ru/api/play/video/%s/' % video_id, display_id)

        item = video_data['playlist']['items'][0]

        title = item['title']
        description = item['description']
        thumbnail = item['thumbnail']
        duration = float_or_none(item.get('durationMilliseconds'), 1000)
        age_limit = parse_age_limit(item.get('ageRestrictions'))

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
