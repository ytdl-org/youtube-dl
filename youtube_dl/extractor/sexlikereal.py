# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
    js_to_json,
)


class SexLikeRealIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sexlikereal\.com/scenes/(?P<display_id>[^/]*)-(?P<id>\d+)'
    _TEST = {
        'url': 'https://www.sexlikereal.com/scenes/wet-college-student-7208',
        'md5': '48e3ac422b783ececec418b12e2ccb56',
        'info_dict': {
            'id': '7208',
            'ext': 'mp4',
            'title': 'Wet College Student',
            'thumbnail': 'https://cdn-vr.sexlikereal.com/images/7208/vr-porn-Wet-College-Student-cover-app.jpg',
            'display_id': "wet-college-student",
            'duration': 122,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')
        webpage = self._download_webpage(url, video_id)

        video_data = self._parse_json(
            self._search_regex(
                r'window\.vrPlayerSettings\s*=\s*({[^;]+});',
                webpage, 'video_data'
            ), video_id, transform_source=js_to_json
        )["videoData"]

        title = (video_data["title"] or (self._html_search_meta('twitter:title',
                 webpage, 'title')).split('-')[0].strip())

        formats = []
        for quality in video_data['src']:
            formats.append({
                'url': quality['url'],
                'ext': determine_ext(quality['mimeType'], 'mp4'),
                'format_id': quality['quality']
            })

        like_count = int_or_none(video_data.get('likes'))
        duration = float_or_none(video_data.get('duration'))

        description = self._html_search_meta(
            ['description', 'twitter:description'], webpage, 'description'
        )

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'thumbnail': video_data.get('posterURL'),
            'like_count': like_count,
            'duration': duration,
            'description': description,
            'formats': formats,
        }
