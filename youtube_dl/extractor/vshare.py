# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VShareIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vshare\.io/[dv]/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://vshare.io/d/0f64ce6',
        'md5': '16d7b8fef58846db47419199ff1ab3e7',
        'info_dict': {
            'id': '0f64ce6',
            'title': 'vl14062007715967',
            'ext': 'mp4',
        }
    }, {
        'url': 'https://vshare.io/v/0f64ce6/width-650/height-430/1',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://vshare.io/d/%s' % video_id, video_id)

        title = self._html_search_regex(
            r'(?s)<div id="root-container">(.+?)<br/>', webpage, 'title')
        video_url = self._search_regex(
            r'<a[^>]+href=(["\'])(?P<url>(?:https?:)?//.+?)\1[^>]*>[Cc]lick\s+here',
            webpage, 'video url', group='url')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
        }
