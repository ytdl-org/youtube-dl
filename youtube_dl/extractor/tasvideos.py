from __future__ import unicode_literals

from .common import InfoExtractor


class TASVideosIE(InfoExtractor):
    _VALID_URL = r'http://tasvideos.org/(?P<id>\d+M)\.html'
    _TEST = {
        'url': 'http://tasvideos.org/4352M.html',
        'md5': '92b08f544beb6ee905030609c7251cd1',
        'info_dict': {
            'id': '4352M',
            'ext': 'mkv',
            'title': 'C64 L\'Abbaye des Morts',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_url = "http://www." + self._search_regex(
            r'<a [^>]+(?P<URL>archive\.org\/download[^<]+\.(?:mkv|mp4|avi))[^<]+<\/a>',
            webpage, 'video url')
        title = self._search_regex(
            r'<span title="Movie[^"]+">(?P<TITLE>[^<]+)<\/span>', webpage,
            'title')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
        }
