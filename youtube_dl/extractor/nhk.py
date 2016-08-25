from __future__ import unicode_literals

from .common import InfoExtractor


class NhkVodIE(InfoExtractor):
    _VALID_URL = r'https?://www3\.nhk\.or\.jp/nhkworld/en/vod/(?P<id>.+?)\.html'
    _TEST = {
        # Videos available only for a limited period of time. Visit
        # http://www3.nhk.or.jp/nhkworld/en/vod/ for working samples.
        'url': 'http://www3.nhk.or.jp/nhkworld/en/vod/tokyofashion/20160815.html',
        'info_dict': {
            'id': 'A1bnNiNTE6nY3jLllS-BIISfcC_PpvF5',
            'ext': 'flv',
            'title': 'TOKYO FASHION EXPRESS - The Kimono as Global Fashion',
            'description': 'md5:db338ee6ce8204f415b754782f819824',
            'series': 'TOKYO FASHION EXPRESS',
            'episode': 'The Kimono as Global Fashion',
        },
        'skip': 'Videos available only for a limited period of time',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        embed_code = self._search_regex(
            r'nw_vod_ooplayer\([^,]+,\s*(["\'])(?P<id>(?:(?!\1).)+)\1',
            webpage, 'ooyala embed code', group='id')

        title = self._search_regex(
            r'<div[^>]+class=["\']episode-detail["\']>\s*<h\d+>([^<]+)',
            webpage, 'title', default=None)
        description = self._html_search_regex(
            r'(?s)<p[^>]+class=["\']description["\'][^>]*>(.+?)</p>',
            webpage, 'description', default=None)
        series = self._search_regex(
            r'<h2[^>]+class=["\']detail-top-player-title[^>]+><a[^>]+>([^<]+)',
            webpage, 'series', default=None)

        return {
            '_type': 'url_transparent',
            'ie_key': 'Ooyala',
            'url': 'ooyala:%s' % embed_code,
            'title': '%s - %s' % (series, title) if series and title else title,
            'description': description,
            'series': series,
            'episode': title,
        }
