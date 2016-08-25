from __future__ import unicode_literals

from .common import InfoExtractor


class NhkVodIE(InfoExtractor):
    _VALID_URL = r'http://www3\.nhk\.or\.jp/nhkworld/en/vod/(?P<id>.+)\.html'
    _TESTS = [{
        'url': 'http://www3.nhk.or.jp/nhkworld/en/vod/tokyofashion/20160815.html',
        'info_dict': {
            'id': 'A1bnNiNTE6nY3jLllS-BIISfcC_PpvF5',
            'ext': 'flv',
            'title': '[nhkworld]VOD;2009-251-2016;TOKYO FASHION EXPRESS;The Kimono as Global Fashion;en',
        },
        'params': {
            'skip_download': True  # Videos available only for a limited period of time.
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        embed_code = self._search_regex(
            r'''nw_vod_ooplayer\('movie-area', '([^']+)'\);''',
            webpage,
            'ooyala embed code')

        return self.url_result('ooyala:' + embed_code, 'Ooyala')
