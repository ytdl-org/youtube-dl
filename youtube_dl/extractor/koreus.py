from __future__ import unicode_literals
from .common import InfoExtractor


class koreusIE(InfoExtractor):
    _VALID_URL = r'https:\/\/www\.koreus\.com/video/(?P<id>\S+)'

    _TESTS = [{
        'url': 'https://www.koreus.com/video/pub-mazda-drague.html',
        'info_dict': {
            'id': 'pub-mazda-drague',
            'ext': 'mp4',
            'title': 'Pub Mazda (Drague)',
        }

    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            url, video_id
        )

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        download_url = self._html_search_regex(

            r'<source src="(https://embed\.koreus\.com/[0-9]+/[0-9]+/[a-z-]+\.mp4)" type="video/mp4"',
            webpage, "download_url"
        )

        return {
            'http_headers': {'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5'},
            'id': video_id,
            'url': download_url,
            'title': title

        }
