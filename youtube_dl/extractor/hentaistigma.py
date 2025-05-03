# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    merge_dicts,
    traverse_obj,
)


class HentaiStigmaIE(InfoExtractor):
    _VALID_URL = r'^https?://hentai\.animestigma\.com/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://hentai.animestigma.com/inyouchuu-etsu-bonus/',
        'md5': '4e3d07422a68a4cc363d8f57c8bf0d23',
        'info_dict': {
            'id': 'inyouchuu-etsu-bonus',
            'ext': 'mp4',
            'title': 'Inyouchuu Etsu Bonus',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<h2[^>]+class="posttitle"[^>]*><a[^>]*>([^<]+)</a>',
            webpage, 'title')

        wrap_url = self._search_regex(
            r'<iframe[^>]+src="([^"]+mp4)"', webpage, 'wrapper url')

        vid_page = self._download_webpage(wrap_url, video_id)

        entries = self._parse_html5_media_entries(wrap_url, vid_page, video_id)
        self._sort_formats(traverse_obj(entries, (0, 'formats')) or [])

        return merge_dicts({
            'id': video_id,
            'title': title,
            'age_limit': 18,
        }, entries[0])
