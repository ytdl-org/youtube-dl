# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class XboxClipsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?xboxclips\.com/\S+?/(?P<id>[a-zA-Z0-9-]{36})'
    _TEST = {
        'url': 'https://xboxclips.com/DeeperGnu613/7936bcb9-83fc-4565-979b-8db96bffa460',
        'md5': 'e434323563f3ae6f02ab1f5b8f514f28',
        'info_dict': {
            'id': '7936bcb9-83fc-4565-979b-8db96bffa460',
            'ext': 'mp4',
            'title': "XboxClips - DeeperGnu613 playing Forza Horizon 4",
            'uploader': 'DeeperGnu613'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_url = self._html_search_regex(
            r"<source src=\"(\S+)\"", webpage, 'URL')
        title = self._html_search_regex(
            r'<title>(.+?)</title>', webpage, 'title', fatal=False)
        uploader = self._html_search_regex(
            r'<h3>(.+?)</h3>', webpage, 'uploader', fatal=False)
        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'url': video_url
        }