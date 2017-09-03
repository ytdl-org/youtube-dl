# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class ManyVidsIE(InfoExtractor):
    _VALID_URL = r'(?i)https?://(?:www\.)?manyvids\.com/video/(?P<id>\d+)'
    _TEST = {
        'url': 'https://www.manyvids.com/Video/133957/everthing-about-me/',
        'md5': '03f11bb21c52dd12a05be21a5c7dcc97',
        'info_dict': {
            'id': '133957',
            'ext': 'mp4',
            'title': 'everthing about me (Preview)',
            'view_count': int,
            'like_count': int,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(
            r'data-(?:video-filepath|meta-video)\s*=s*(["\'])(?P<url>(?:(?!\1).)+)\1',
            webpage, 'video URL', group='url')

        title = '%s (Preview)' % self._html_search_regex(
            r'<h2[^>]+class="m-a-0"[^>]*>([^<]+)', webpage, 'title')

        like_count = int_or_none(self._search_regex(
            r'data-likes=["\'](\d+)', webpage, 'like count', default=None))
        view_count = int_or_none(self._html_search_regex(
            r'(?s)<span[^>]+class="views-wrapper"[^>]*>(.+?)</span', webpage,
            'view count', default=None))

        return {
            'id': video_id,
            'title': title,
            'view_count': view_count,
            'like_count': like_count,
            'formats': [{
                'url': video_url,
            }],
        }
