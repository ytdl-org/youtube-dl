from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlencode
from ..utils import (
    ExtractorError,
    unescapeHTML,
    unified_strdate
)


class EroProfileIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?eroprofile\.com/m/videos/view/(?P<id>[^/]+)'
    _LOGIN_URL = 'https://www.eroprofile.com/ajax_v1.php'
    _NETRC_MACHINE = 'eroprofile'
    _TESTS = [{
        'url': 'https://www.eroprofile.com/m/videos/view/Farting-in-leather-trousers',
        'md5': 'f3ea883be7a342cd0d03e69772f186d3',
        'info_dict': {
            'id': '8452925',
            'display_id': 'Farting-in-leather-trousers',
            'upload_date': '20190423',
            'description': 'Join your fellow fart aficionados over on Reddit at r/peefarts and r/girlsfarting',
            'uploader': 'ukfartgirllover',
            'title': 'Farting in leather trousers',
            'ext': 'm4v',
            'thumbnail': r're:https?://.*\.jpg.*',
            'age_limit': 18,
        }
    }, {
        'url': 'https://www.eroprofile.com/m/videos/view/Strict-Teacher-Huge-Cumshot-Over-Black-Leather-Skirt-YummyCouple-com',
        'md5': '5562113ca7cac4bfb989032dcd21c49e',
        'info_dict': {
            'id': '9998587',
            'display_id': 'Strict-Teacher-Huge-Cumshot-Over-Black-Leather-Skirt-YummyCouple-com',
            'upload_date': '20201230',
            'description': None,
            'uploader': 'MrSunshine',
            'title': 'Strict Teacher Huge Cumshot Over Black Leather Skirt - YummyCouple.com',
            'ext': 'm4v',
            'thumbnail': r're:https?://.*\.jpg.*',
            'age_limit': 18,
        },
        'skip': 'Requires login',
    }]

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        query = compat_urllib_parse_urlencode({
            'username': username,
            'password': password,
            'url': 'https://www.eroprofile.com/',
        })
        login_url = self._LOGIN_URL + query
        login_page = self._download_webpage(login_url, None, False)

        m = re.search(r'Your username or password was incorrect\.', login_page)
        if m:
            raise ExtractorError(
                'Wrong username and/or password.', expected=True)

        self.report_login()
        redirect_url = self._search_regex(
            r'<script[^>]+?src="([^"]+)"', login_page, 'login redirect url')
        self._download_webpage(redirect_url, None, False)

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        m = re.search(r'You must be logged in to view this video\.', webpage)
        if m:
            self.raise_login_required('This video requires login')

        video_id = self._search_regex(
            [r"glbUpdViews\s*\('\d*','(\d+)'", r'p/report/video/(\d+)'],
            webpage, 'video id', default=None)

        video_url = unescapeHTML(self._search_regex(
            r'<source src="([^"]+)', webpage, 'video url'))

        title = self._html_search_regex(
            r'<h1 class="capMultiLine">(.*?)</h1>', webpage, 'title')

        uploader = self._html_search_regex(
            r'<div.*?>Uploaded by</div>.*?<div.*?<a .*?>(.*?)</a>',
            webpage, 'uploader', fatal=False, flags=re.DOTALL)

        description = self._html_search_regex(
            r'<h1 class="capMultiLine">.*?</h1>.*?<p>(.*?)</p>.*?<div.*?>Uploaded by</div>',
            webpage, 'description', default=None, flags=re.DOTALL)

        categories = self._html_search_regex(
            r'<div.*?>Niche</div>.*?<div.*?<a .*?>(.*?)</a>',
            webpage, 'description', fatal=False, flags=re.DOTALL)

        thumbnail = self._search_regex(
            r'<video.*? poster="([^"]+)',
            webpage, 'thumbnail', fatal=False, flags=re.DOTALL)

        upload_date = unified_strdate(self._html_search_regex(
            r'<div.*?>Upload date</div>.*?<div.*?>(.*?)<span',
            webpage, 'thumbnail', fatal=False, flags=re.DOTALL))

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'description': description,
            'categories': [categories],
            'upload_date': upload_date,
            'age_limit': 18,
        }
