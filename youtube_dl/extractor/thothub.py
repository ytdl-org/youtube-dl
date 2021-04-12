# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ThothubIE(InfoExtractor):
    _VALID_URL = r'https?://thothub\.wtf/(?P<id>[\w-]+)/'
    _TESTS = [{
        'url': 'https://thothub.wtf/belle-delphine-christmas-porn-full-video-leaked/',
        'md5': 'c6fb6c3e1a7a69e8b50104d1cc7fe627',
        'info_dict': {
            'id': 'belle-delphine-christmas-porn-full-video-leaked',
            'ext': 'mp4',
            'title': 'Watch Belle Delphine Christmas Porn Full Video Leaked full video on Thothub Thothub.wtf',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage_url = 'https://thothub.wtf/' + video_id
        webpage = self._download_webpage(webpage_url, video_id, 'Download webpage')

        iframe_url = self._html_search_regex(r'<IFRAME SRC="(.+?)"', webpage, u'iframe URL')
        # print('iframe_url:', iframe_url)
        iframe = self._download_webpage(iframe_url, video_id, 'Download frame')

        playlist_url = self._html_search_regex(r'<source src="(.+?)"', iframe, u'playlist URL')
        # print('playlist_url:', playlist_url)

        title = self._og_search_title(webpage).encode('ascii', errors='ignore').decode().strip()
        # print('title:', title)

        return {
            'id': video_id,
            'url': playlist_url,
            'title': title or 'Thothub Video',
            'ext': 'mp4',
        }
