from __future__ import unicode_literals

from .youtube import YoutubeIE
from .jwplatform import JWPlatformBaseIE


class WimpIE(JWPlatformBaseIE):
    _VALID_URL = r'https?://(?:www\.)?wimp\.com/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://www.wimp.com/maru-is-exhausted/',
        'md5': 'ee21217ffd66d058e8b16be340b74883',
        'info_dict': {
            'id': 'maru-is-exhausted',
            'ext': 'mp4',
            'title': 'Maru Is Exhausted.',
            'description': 'md5:57e099e857c0a4ea312542b684a869b8',
        }
    }, {
        'url': 'http://www.wimp.com/clowncar/',
        'md5': '4e2986c793694b55b37cf92521d12bb4',
        'info_dict': {
            'id': 'clowncar',
            'ext': 'mp4',
            'title': 'It\'s Like A Clown Car.',
            'description': 'Gretchen Hoey raises Basset Hounds and on this particular day, she catches a few of them snuggling together in one doghouse. After one of them notices her, they all begin to funnel out of the doghouse like clowns in a clown car to greet her.'
        },
        'add_ie': ['Youtube'],
    }, {
        'url': 'http://www.wimp.com/bird-does-funny-march/',
        'md5': 'f2833774cf4d680849989a1cf92a06cc',
        'info_dict': {
            'id': 'bird-does-funny-march',
            'ext': 'mp4',
            'title': 'Bird Does Funny March',
            'description': 'This bird\'s walk might look pretty silly, but as soon as you add some military marching music over it, it becomes the most regal sight you\'ve ever seen.\r\n'
        }
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

        url = self._search_regex(r'class=\'oyt-container .*? data-src=\'(.*?)\'', webpage, 'Video URL', default=None, fatal=False)

        if url:
            info_dict = {
                'id': video_id,
                'title': self._og_search_title(webpage),
                'description': self._og_search_description(webpage),
                'url': url
            }
        else:
            info_dict = self._extract_jwplayer_data(
                webpage, video_id, require_title=False)

            info_dict.update({
                'id': video_id,
                'title': self._og_search_title(webpage),
                'description': self._og_search_description(webpage),
            })

        return info_dict
