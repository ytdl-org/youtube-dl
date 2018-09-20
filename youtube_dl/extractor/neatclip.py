# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class NeatclipIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?neatclip\.com/clip/(?P<id>[a-z0-9]+)'
    _TESTS = [
        {
            'url': 'https://neatclip.com/clip/q8n74r9eg',
            'md5': 'b9f49690141d1aa35d48f6bd27102956',
            'info_dict': {
                'id': 'q8n74r9eg',
                'ext': 'mp4',
                'title': 'Allu 1v2 with KQLY shot',
                'thumbnail': r're:^https?://.*\.png$',
            }
        },
        {
            'url': 'https://neatclip.com/clip/48glvl7ew',
            'md5': '2b2629e1f2677787b67f9d34071ee57e',
            'info_dict': {
                'id': '48glvl7ew',
                'ext': 'mp4',
                'title': 'DansGaming notices something fishy',
                'thumbnail': r're:^https?://.*\.png$',
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<meta property="og:title" content="(.+?)" />', webpage, 'title').replace(" - NeatClip", "")
        url = self._html_search_regex(
            r'<meta property="og:video:url" content="(.+?)" />', webpage, 'url')
        thumbnail = self._html_search_regex(
            r'<meta property="og:image" content="(.+?)" />', webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'url': url,
            'thumbnail': thumbnail
        }
