# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class KaraoketvIE(InfoExtractor):
    '''
    In api_play.php there's a video-cdn.com <iframe>. The latter plays an
    unencrypted RTMP stream. However I can't download it with rtmpdump.
    '''
    _WORKING = False

    _VALID_URL = r'http://www.karaoketv.co.il/[^/]+/(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.karaoketv.co.il/%D7%A9%D7%99%D7%A8%D7%99_%D7%A7%D7%A8%D7%99%D7%95%D7%A7%D7%99/58356/%D7%90%D7%99%D7%96%D7%95%D7%9F',
        'info_dict': {
            'id': '58356',
            'ext': 'flv',
            'title': 'קריוקי של איזון',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        api_page_url = self._html_search_regex(
            r'<iframe[^>]+src="(http://www.karaoke.co.il/api_play.php?[^"]+)"',
            webpage, 'API play URL')

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'title': self._og_search_title(webpage),
            'url': api_page_url,
        }
