from __future__ import unicode_literals

from .common import InfoExtractor
from .youtube import YoutubeIE


class WimpIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?wimp\.com/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://www.wimp.com/maruexhausted/',
        'md5': 'ee21217ffd66d058e8b16be340b74883',
        'info_dict': {
            'id': 'maruexhausted',
            'ext': 'mp4',
            'title': 'Maru is exhausted.',
            'description': 'md5:57e099e857c0a4ea312542b684a869b8',
        }
    }, {
        'url': 'http://www.wimp.com/clowncar/',
        'md5': '4e2986c793694b55b37cf92521d12bb4',
        'info_dict': {
            'id': 'clowncar',
            'ext': 'webm',
            'title': 'It\'s like a clown car.',
            'description': 'md5:0e56db1370a6e49c5c1d19124c0d2fb2',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        youtube_id = self._search_regex(
            r"videoId\s*:\s*[\"']([0-9A-Za-z_-]{11})[\"']",
            webpage, 'video URL', default=None)
        if youtube_id:
            return {
                '_type': 'url',
                'url': youtube_id,
                'ie_key': YoutubeIE.ie_key(),
            }

        video_url = self._search_regex(
            r'<video[^>]+>\s*<source[^>]+src=(["\'])(?P<url>.+?)\1',
            webpage, 'video URL', group='url')

        return {
            'id': video_id,
            'url': video_url,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
        }
