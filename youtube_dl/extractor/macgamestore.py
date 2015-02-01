from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class MacGameStoreIE(InfoExtractor):
    IE_NAME = 'macgamestore'
    IE_DESC = 'MacGameStore trailers'
    _VALID_URL = r'https?://www\.macgamestore\.com/mediaviewer\.php\?trailer=(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.macgamestore.com/mediaviewer.php?trailer=2450',
        'md5': '8649b8ea684b6666b4c5be736ecddc61',
        'info_dict': {
            'id': '2450',
            'ext': 'm4v',
            'title': 'Crow',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            url, video_id, 'Downloading trailer page')

        if '>Missing Media<' in webpage:
            raise ExtractorError(
                'Trailer %s does not exist' % video_id, expected=True)

        video_title = self._html_search_regex(
            r'<title>MacGameStore: (.*?) Trailer</title>', webpage, 'title')

        video_url = self._html_search_regex(
            r'(?s)<div\s+id="video-player".*?href="([^"]+)"\s*>',
            webpage, 'video URL')

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title
        }
