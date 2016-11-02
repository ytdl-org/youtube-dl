# coding: utf-8
from __future__ import unicode_literals

from .anvato import AnvatoIE
from .sendtonews import SendtoNewsIE
from ..compat import compat_urlparse
from ..utils import unified_timestamp


class CBSLocalIE(AnvatoIE):
    _VALID_URL = r'https?://[a-z]+\.cbslocal\.com/\d+/\d+/\d+/(?P<id>[0-9a-z-]+)'

    _TESTS = [{
        # Anvato backend
        'url': 'http://losangeles.cbslocal.com/2016/05/16/safety-advocates-say-fatal-car-seat-failures-are-public-health-crisis',
        'md5': 'f0ee3081e3843f575fccef901199b212',
        'info_dict': {
            'id': '3401037',
            'ext': 'mp4',
            'title': 'Safety Advocates Say Fatal Car Seat Failures Are \'Public Health Crisis\'',
            'description': 'Collapsing seats have been the focus of scrutiny for decades, though experts say remarkably little has been done to address the issue. Randy Paige reports.',
            'thumbnail': 're:^https?://.*',
            'timestamp': 1463440500,
            'upload_date': '20160516',
            'subtitles': {
                'en': 'mincount:5',
            },
            'categories': [
                'Stations\\Spoken Word\\KCBSTV',
                'Syndication\\MSN',
                'Syndication\\NDN',
                'Syndication\\AOL',
                'Syndication\\Yahoo',
                'Syndication\\Tribune',
                'Syndication\\Curb.tv',
                'Content\\News'
            ],
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
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        sendtonews_url = SendtoNewsIE._extract_url(webpage)
        if sendtonews_url:
            return self.url_result(
                compat_urlparse.urljoin(url, sendtonews_url),
                ie=SendtoNewsIE.ie_key())

        info_dict = self._extract_anvato_videos(webpage, display_id)

        time_str = self._html_search_regex(
            r'class="entry-date">([^<]+)<', webpage, 'released date', fatal=False)
        timestamp = unified_timestamp(time_str)

        info_dict.update({
            'display_id': display_id,
            'timestamp': timestamp,
        })

        return info_dict
