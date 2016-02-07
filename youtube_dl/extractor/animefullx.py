# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class AnimefullxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?animefullx\.com/watch/(?P<id>([a-zA-Z0-9-]+)?\d+)'
    _TESTS = [{
        'url': 'http://www.animefullx.com/watch/chobits-episode-1/',
        'md5': '48615cd86808a814d67f095c607c9435',
        'info_dict': {
            'id': 'chobits-episode-1',
            'ext': 'mp4',
            'title': 'Watch Chobits Episode 1 English Subbed Online - Animefullx',
        },
    }, {
        'url': 'http://www.animefullx.com/watch/ao-no-exorcist-episode-1/',
        'md5': '913b370e9568ab2c53733d6ebf9c2bcd',
        'info_dict': {
            'id': 'ao-no-exorcist-episode-1',
            'ext': 'mp4',
            'title': 'Watch Ao no Exorcist Episode 1 English Subbed Online - Animefullx',
        }
    }, {
        'url': 'http://www.animefullx.com/watch/8-man-after-episode-1/',
        'md5': 'b57f34b03cd37e7fb5530337802e9a4a',
        'info_dict': {
            'id': '8-man-after-episode-1',
            'ext': 'mp4',
            'title': 'Watch 8 Man After Episode 1 English Subbed Online - Animefullx',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        scripturl = self._html_search_regex(r'<iframe src="([^"]+)"', webpage, u'script URL')

        if ( scripturl[ 0 ] == '/' ):
            script = self._download_webpage( 'http://www.animefullx.com/'+scripturl[1:], '' )
        if ( 'http' in scripturl ):
            script = self._download_webpage( scripturl, '' )

        video_url = self._html_search_regex(r'file:\ ?"([^"]+)"', script, u'video URL')

        return {
            '_type': 'video',
            'id': video_id,
            'url': video_url,
            'title': self._og_search_title( webpage ),
            'ext': 'mp4',
        }