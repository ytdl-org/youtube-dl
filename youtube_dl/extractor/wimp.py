from __future__ import unicode_literals

from .common import InfoExtractor
from .youtube import YoutubeIE


class WimpIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?wimp\.com/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://www.wimp.com/maru-is-exhausted/',
        'md5': 'ee21217ffd66d058e8b16be340b74883',
        'info_dict': {
            'id': 'maru-is-exhausted',
            'ext': 'mp4',
            'title': 'Maru is exhausted.',
            'description': 'md5:57e099e857c0a4ea312542b684a869b8',
        }
    }, {
        'url': 'http://www.wimp.com/clowncar/',
        'md5': '5c31ad862a90dc5b1f023956faec13fe',
        'info_dict': {
            'id': 'cG4CEr2aiSg',
            'ext': 'webm',
            'title': 'Basset hound clown car...incredible!',
            'description': '5 of my Bassets crawled in this dog loo! www.bellinghambassets.com\n\nFor licensing/usage please contact: licensing(at)jukinmediadotcom',
            'upload_date': '20140303',
            'uploader': 'Gretchen Hoey',
            'uploader_id': 'gretchenandjeff1',
        },
        'add_ie': ['Youtube'],
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

        info_dict = self._extract_jwplayer_data(
            webpage, video_id, require_title=False)

        info_dict.update({
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
        })

        return info_dict
