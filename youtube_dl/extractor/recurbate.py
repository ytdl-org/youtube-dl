# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class RecurbateIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?recurbate\.com\/play\.php\?video=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://recurbate.com/play.php?video=38825900',
        'info_dict': {
            'id': '38825900',
            'ext': 'mp4',
            'title': 'Performer vvendy show on 2022-10-21 16:55, Chaturbate Archive – Recurbate'
        },
        'skip': 'Requires premium subscription cookie session',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')
        token = self._html_search_regex(r'data-token=(.+?")', webpage, 'play_button').strip("\"")
        get_url = f"https://recurbate.com/api/get.php?video={video_id}&token={token}"
        video_webpage = self._download_webpage(get_url, video_id)
        real_url = self._html_search_regex(r'<source src=(.+?) type=\"video\/mp4\"', video_webpage, 'mp4video').strip("\"")

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'url': real_url,
        }
