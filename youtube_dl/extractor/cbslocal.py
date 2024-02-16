# coding: utf-8
from __future__ import unicode_literals

from .anvato import AnvatoIE
from .sendtonews import SendtoNewsIE
from ..compat import compat_urlparse
from ..utils import (
    merge_dicts,
    parse_iso8601,
    unified_timestamp,
)


class CBSLocalIE(AnvatoIE):
    _VALID_URL_BASE = r'https?://[a-z]+\.cbslocal\.com/'
    _VALID_URL = _VALID_URL_BASE + r'video/(?P<id>\d+)'

    _OLD_ANVATO_KEY = 'anvato_cbslocal_app_web_prod_547f3e49241ef0e5d30c79b2efbca5d92c698f67'

    _TESTS = [{
        'url': 'http://newyork.cbslocal.com/video/3580809-a-very-blue-anniversary/',
        'info_dict': {
            'id': '3580809',
            'ext': 'mp4',
            'title': 'A Very Blue Anniversary',
            'description': 'CBS2’s Cindy Hsu has more.',
            'thumbnail': 're:^https?://.*',
            'timestamp': int,
            'upload_date': r're:^\d{8}$',
            'uploader': 'CBS',
            'subtitles': {
                'en': 'mincount:5',
            },
            'categories': [
                'Stations\\Spoken Word\\WCBSTV',
                'Content\\News',
                'Content\\News\\Local News',
            ],
            'tags': ['CBS 2 News Weekends', 'Cindy Hsu', 'Blue Man Group'],
        },
        'params': {
            'skip_download': True,
        },
        'expected_warnings': ('Failed to download m3u8 information', ),
    }]

    def _real_extract(self, url):

        mcp_id = self._match_id(url)
        webpage = self._download_webpage(url, mcp_id)

        json_ld = self._search_json_ld(webpage, mcp_id, fatal=False) or {}
        json_ld.pop('url', None)

        return merge_dicts(
            self._extract_anvato_videos(webpage, mcp_id)
            or self.url_result(self._OLD_ANVATO_KEY + ':' + mcp_id, 'Anvato', mcp_id),
            json_ld)


class CBSLocalArticleIE(AnvatoIE):
    _VALID_URL = CBSLocalIE._VALID_URL_BASE + r'\d+/\d+/\d+/(?P<id>[0-9a-z-]+)'

    _TESTS = [{
        # Anvato backend
        'url': 'http://losangeles.cbslocal.com/2016/05/16/safety-advocates-say-fatal-car-seat-failures-are-public-health-crisis',
        'only_matching': True
    }, {
        'url': 'https://losangeles.cbslocal.com/2022/02/16/rams-super-bowl-parade-to-take-place-wednesday/',
        'md5': '36bdac3fb24ec8a6d7790218a0357b08',
        'info_dict': {
            'id': '6201053',
            'ext': 'mp4',
            'display_id': 'rams-super-bowl-parade-to-take-place-wednesday',
            'upload_date': '20220216',
            'uploader': 'CBS',
            'description': 'Jeff Nguyen is live from outside the L.A. Memorial Coliseum where fans cheered on the Los Angeles Rams.',
            'timestamp': 1645044990,
            'title': 'Rams Fans Gather Outside The LA Memorial Coliseum',
            'categories': [
                'Stations\\Spoken Word\\KCALTV',
                'Content\\News',
                'Content\\Top Story',
            ],
            'tags': ['KCAL 9 News Afternoon'],
        },
    }, {
        # SendtoNews embed
        'url': 'http://cleveland.cbslocal.com/2016/05/16/indians-score-season-high-15-runs-in-blowout-win-over-reds-rapid-reaction/',
        'info_dict': {
            'id': 'GxfCe0Zo7D-175909-5588',
        },
        'playlist_count': 9,
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'skip': 'Redirects to CBS News home page',
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        json_ld = self._search_json_ld(webpage, display_id, fatal=False) or {}
        json_ld.pop('url', None)

        sendtonews_url = SendtoNewsIE._extract_url(webpage)
        if sendtonews_url:
            result = self.url_result(
                compat_urlparse.urljoin(url, sendtonews_url),
                ie=SendtoNewsIE.ie_key())
            return merge_dicts(result, json_ld)

        # returns a dict, or raises
        info_dict = self._extract_anvato_videos(webpage, display_id)

        timestamp = unified_timestamp(self._html_search_regex(
            r'class="(?:entry|post)-date"[^>]*>([^<]+)', webpage,
            'released date', default=None)) or parse_iso8601(
            self._html_search_meta('uploadDate', webpage))

        return merge_dicts(
            info_dict,
            json_ld,
            {
                'display_id': display_id,
                'timestamp': timestamp,
            })
