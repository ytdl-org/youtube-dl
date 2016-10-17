from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class ViceIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?vice\.com/(?:[^/]+/)?videos?/(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'http://www.vice.com/video/cowboy-capitalists-part-1',
        'info_dict': {
            'id': '43cW1mYzpia9IlestBjVpd23Yu3afAfp',
            'ext': 'flv',
            'title': 'VICE_COWBOYCAPITALISTS_PART01_v1_VICE_WM_1080p.mov',
            'duration': 725.983,
        },
    }, {
        'url': 'http://www.vice.com/video/how-to-hack-a-car',
        'md5': '6fb2989a3fed069fb8eab3401fc2d3c9',
        'info_dict': {
            'id': '3jstaBeXgAs',
            'ext': 'mp4',
            'title': 'How to Hack a Car: Phreaked Out (Episode 2)',
            'description': 'md5:ee95453f7ff495db8efe14ae8bf56f30',
            'uploader_id': 'MotherboardTV',
            'uploader': 'Motherboard',
            'upload_date': '20140529',
        },
    }, {
        'url': 'https://news.vice.com/video/experimenting-on-animals-inside-the-monkey-lab',
        'only_matching': True,
    }, {
        'url': 'http://www.vice.com/ru/video/big-night-out-ibiza-clive-martin-229',
        'only_matching': True,
    }, {
        'url': 'https://munchies.vice.com/en/videos/watch-the-trailer-for-our-new-series-the-pizza-show',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        try:
            embed_code = self._search_regex(
                r'embedCode=([^&\'"]+)', webpage,
                'ooyala embed code', default=None)
            if embed_code:
                return self.url_result('ooyala:%s' % embed_code, 'Ooyala')
            youtube_id = self._search_regex(
                r'data-youtube-id="([^"]+)"', webpage, 'youtube id')
            return self.url_result(youtube_id, 'Youtube')
        except ExtractorError:
            raise ExtractorError('The page doesn\'t contain a video', expected=True)


class ViceShowIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?vice\.com/(?:[^/]+/)?show/(?P<id>[^/?#&]+)'

    _TEST = {
        'url': 'https://munchies.vice.com/en/show/fuck-thats-delicious-2',
        'info_dict': {
            'id': 'fuck-thats-delicious-2',
            'title': "Fuck, That's Delicious",
            'description': 'Follow the culinary adventures of rapper Action Bronson during his ongoing world tour.',
        },
        'playlist_count': 17,
    }

    def _real_extract(self, url):
        show_id = self._match_id(url)
        webpage = self._download_webpage(url, show_id)

        entries = [
            self.url_result(video_url, ViceIE.ie_key())
            for video_url, _ in re.findall(
                r'<h2[^>]+class="article-title"[^>]+data-id="\d+"[^>]*>\s*<a[^>]+href="(%s.*?)"'
                % ViceIE._VALID_URL, webpage)]

        title = self._search_regex(
            r'<title>(.+?)</title>', webpage, 'title', default=None)
        if title:
            title = re.sub(r'(.+)\s*\|\s*.+$', r'\1', title).strip()
        description = self._html_search_meta('description', webpage, 'description')

        return self.playlist_result(entries, show_id, title, description)
