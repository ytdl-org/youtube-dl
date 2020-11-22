# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class XboxClipsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:xboxclips\.com|gameclips\.io)/\S+?/(?P<id>[a-zA-Z0-9-]{36})'
    _TESTS = [{
        'url': 'https://xboxclips.com/DeeperGnu613/7936bcb9-83fc-4565-979b-8db96bffa460',
        'md5': 'e434323563f3ae6f02ab1f5b8f514f28',
        'info_dict': {
            'id': '7936bcb9-83fc-4565-979b-8db96bffa460',
            'ext': 'mp4',
            'title': 'GameClips.io - DeeperGnu613 playing Forza Horizon 4. Watch more Xbox Clips at GameClips.io',
            'uploader': 'DeeperGnu613'
        }
    }, {
        'url': 'https://gameclips.io/Wrecked559/f34f0f4d-65f8-456e-aeaa-7da8a108a658',
        'md5': '9d50e531a957b2f823720a0c1aefaea4',
        'info_dict': {
            'id': 'f34f0f4d-65f8-456e-aeaa-7da8a108a658',
            'ext': 'mp4',
            'title': 'GameClips.io - Wrecked559 playing Call of Duty®: Modern Warfare®. Watch more Xbox Clips at GameClips.io',
            'uploader': 'Wrecked559'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_url = self._html_search_regex(
            r'<source src="(\S+)"', webpage, 'URL')
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
