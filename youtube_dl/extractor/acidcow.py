from __future__ import unicode_literals

from .common import InfoExtractor


class acidcowIE(InfoExtractor):
    """
    InfoExtractor for acid.cow
    This class should be used to handle videos. Another class (TODO) will be
    used to implement playlists or other content.
    """

    _VALID_URL = r'https?://acidcow\.com/video/(?P<id>\d+)-\S+'

    _TESTS = [{
        'url': 'https://acidcow.com/video/118851-learning_to_follow_patterns_with_dad.html',
        'info_dict': {
            'id': '118851',
            'ext': 'mp4',
            'title': 'learning_to_follow_patterns_with_dad',

        },
    }, {
        'url': 'https://acidcow.com/video/116642-that_was_really_close.html',
        'info_dict': {
            'id': '116642',
            'ext': 'mp4',
            'title': 'that_was_really_close',
        },
    }, {
        'url': 'https://acidcow.com/video/118850-it_reminds_me_of_cars_scene.html',
        'info_dict': {
            'id': '118850',
            'ext': 'mp4',
            'title': 'it_reminds_me_of_cars_scene',
        }

    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            url, video_id
        )

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        download_url = self._html_search_regex(

            r'(https://cdn\.acidcow\.com/pics/[0-9]+/video/\S+\.mp4)',

            webpage, "download_url"
        )
        return {
            'id': video_id,
            'url': download_url,
            'title': title
        }
