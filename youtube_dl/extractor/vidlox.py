# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VidloxIE(InfoExtractor):
    _VALID_URL = r'https?://vidlox\.tv(/embed-|/)(?P<id>[0-9a-z]+)(\.html)?'
    _TESTS = [{
        'url': 'https://vidlox.tv/nc11cfucpp3m',
        'md5': 'e3a7e1b5edee55570e35fd7641ffb174',
        'info_dict': {
            'id': 'nc11cfucpp3m',
            'ext': 'mp4',
            'title': 'Tetris cyka',
        }
    }, {
        'url': 'https://vidlox.tv/embed-nc11cfucpp3m.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'https://vidlox.tv/' + video_id
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(
            r'<h1([^>]*?)>(?P<title>.+)',
            webpage, 'title', group=2)
        m3u = self._html_search_regex(
            r'sources:([\s]+?)\["(?P<url>.+?)",',
            webpage, 'm3u', group=2)
        formats = self._extract_m3u8_formats(m3u, video_id, ext='mp4', entry_protocol='m3u8_native', m3u8_id='hls', fatal=False)
        return {
            'id': video_id,
            'title': title,
            'formats': formats
        }
