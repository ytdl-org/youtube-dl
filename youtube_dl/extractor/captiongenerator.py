# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class CaptionGeneratorIE(InfoExtractor):
    _VALID_URL = r'(?:https?://(?:www\.)?captiongenerator\.com/(?P<id>[0-9]+))'
    _TESTS = [{
        'url': 'https://www.captiongenerator.com/128/Team-building',
        'info_dict': {
            'id': '128',
            'ext': 'mp4',
            'title': 'Team building...',
            'http_headers': {'Referer': 'https://www.captiongenerator.com/'}
        },
    }, {
        'url': 'https://www.captiongenerator.com/2153287/Man-finds-phone',
        'info_dict': {
            'id': '2153287',
            'ext': 'mp4',
            'title': 'Man finds phone',
            'http_headers': {'Referer': 'https://www.captiongenerator.com/'}
        },
    }, {
        'url': 'https://www.captiongenerator.com/2140517/Haavisto-Pietarissa',
        'info_dict': {
            'id': '2140517',
            'ext': 'mp4',
            'title': 'Haavisto Pietarissa',
            'http_headers': {'Referer': 'https://www.captiongenerator.com/'}
        },
    }, {
        'url': 'https://www.captiongenerator.com/2153147/81-Pay',
        'info_dict': {
            'id': '2153147',
            'ext': 'mp4',
            'title': '81 Pay',
            'http_headers': {'Referer': 'https://www.captiongenerator.com/'}
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_url = self._html_search_regex(r'(https?://[a-z0-9]+\.cloudfront\.net/.+?\.mp4)', webpage, 'videoUrl')
        print(video_url)

        vtt_page = self._download_webpage('https://www.captiongenerator.com/videos/%s.vtt' % video_id, video_id)

        vtt_captions = open("128.vtt", "w")
        vtt_captions.write(vtt_page)
        vtt_captions.close()

        title = self._html_search_regex(r'<title>(.*)</title>', webpage, 'videoTitle')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'http_headers': {"Referer": "https://www.captiongenerator.com/"}
        }
