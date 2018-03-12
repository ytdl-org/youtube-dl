from __future__ import unicode_literals

from .common import InfoExtractor
from .ooyala import OoyalaIE


class TastyTradeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tastytrade\.com/tt/(?:shows|daily_recaps)/[^/]+/episodes/(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'https://www.tastytrade.com/tt/shows/market-measures/episodes/correlation-in-short-volatility-06-28-2017',
        'info_dict': {
            'id': '8xZW5xYjE6aLXhPwseCpyIf50oQw69JM',
            'ext': 'mp4',
            'title': 'Correlation in Short Volatility',
            'description': '[Correlation](https://www.tastytrade.com/tt/learn/correlation) is always changing and positions can be more correlated than we suspect. We can even have...',
            'duration': 753.0,
            'upload_date': '20170628',
            'timestamp': 1498608000,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Ooyala'],
    }, {
        'url': 'https://www.tastytrade.com/tt/shows/daily-dose/episodes/daily-dose-06-30-2017',
        'only_matching': True,
    }, {
        'url': 'https://www.tastytrade.com/tt/daily_recaps/2018-03-09/episodes/soybeans-corn-its-planting-time-03-09-2018',
        'info_dict': {
            'id': 'lud3BtZTE6vnRdolxKRlwNoZQvb3z_LT',
            'ext': 'mp4',
            'title': 'TTL_CTGFE_180309_SEG_EDIT.mp4',
            'description': 'md5:d41d8cd98f00b204e9800998ecf8427e',
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Ooyala'],
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        ooyala_code = self._search_regex(
            r'data-media-id=(["\'])(?P<code>(?:(?!\1).)+)\1',
            webpage, 'ooyala code', group='code')

        info = self._search_json_ld(webpage, display_id, default={})

        info.update({
            '_type': 'url_transparent',
            'ie_key': OoyalaIE.ie_key(),
            'url': 'ooyala:%s' % ooyala_code,
            'display_id': display_id,
        })
        return info
