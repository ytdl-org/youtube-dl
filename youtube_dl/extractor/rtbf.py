# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unescapeHTML,
)


class RTBFIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rtbf\.be/(?:video/[^?]+\?.*\bid=|ouftivi/(?:[^/]+/)*[^?]+\?.*\bvideoId=)(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.rtbf.be/video/detail_les-diables-au-coeur-episode-2?id=1921274',
        'md5': '799f334ddf2c0a582ba80c44655be570',
        'info_dict': {
            'id': '1921274',
            'ext': 'mp4',
            'title': 'Les Diables au coeur (épisode 2)',
            'duration': 3099,
        }
    }, {
        # geo restricted
        'url': 'http://www.rtbf.be/ouftivi/heros/detail_scooby-doo-mysteres-associes?id=1097&videoId=2057442',
        'only_matching': True,
    }, {
        'url': 'http://www.rtbf.be/ouftivi/niouzz?videoId=2055858',
        'only_matching': True,
    }]

    _QUALITIES = [
        ('mobile', 'mobile'),
        ('web', 'SD'),
        ('url', 'MD'),
        ('high', 'HD'),
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://www.rtbf.be/video/embed?id=%s' % video_id, video_id)

        data = self._parse_json(
            unescapeHTML(self._search_regex(
                r'data-media="([^"]+)"', webpage, 'data video')),
            video_id)

        if data.get('provider').lower() == 'youtube':
            video_url = data.get('downloadUrl') or data.get('url')
            return self.url_result(video_url, 'Youtube')
        formats = []
        for key, format_id in self._QUALITIES:
            format_url = data['sources'].get(key)
            if format_url:
                formats.append({
                    'format_id': format_id,
                    'url': format_url,
                })

        return {
            'id': video_id,
            'formats': formats,
            'title': data['title'],
            'description': data.get('description') or data.get('subtitle'),
            'thumbnail': data.get('thumbnail'),
            'duration': data.get('duration') or data.get('realDuration'),
            'timestamp': int_or_none(data.get('created')),
            'view_count': int_or_none(data.get('viewCount')),
        }
