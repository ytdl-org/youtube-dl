# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    get_element_by_class,
    urlencode_postdata,
)


class NJPWWorldIE(InfoExtractor):
    _VALID_URL = r'https?://njpwworld\.com/p/(?P<id>[a-z0-9_]+)'
    IE_DESC = '新日本プロレスワールド'
    _NETRC_MACHINE = 'njpwworld'

    _TEST = {
        'url': 'http://njpwworld.com/p/s_series_00155_1_9/',
        'info_dict': {
            'id': 's_series_00155_1_9',
            'ext': 'mp4',
            'title': '第9試合　ランディ・サベージ　vs　リック・スタイナー',
            'tags': list,
        },
        'params': {
            'skip_download': True,  # AES-encrypted m3u8
        },
        'skip': 'Requires login',
    }

    def _real_initialize(self):
        self._login()

    def _login(self):
        username, password = self._get_login_info()
        # No authentication to be performed
        if not username:
            return True

        webpage, urlh = self._download_webpage_handle(
            'https://njpwworld.com/auth/login', None,
            note='Logging in', errnote='Unable to login',
            data=urlencode_postdata({'login_id': username, 'pw': password}))
        # /auth/login will return 302 for successful logins
        if urlh.geturl() == 'https://njpwworld.com/auth/login':
            self.report_warning('unable to login')
            return False

        return True

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        formats = []
        for player_url, kind in re.findall(r'<a[^>]+href="(/player[^"]+)".+?<img[^>]+src="[^"]+qf_btn_([^".]+)', webpage):
            player_url = compat_urlparse.urljoin(url, player_url)

            player_page = self._download_webpage(
                player_url, video_id, note='Downloading player page')

            entries = self._parse_html5_media_entries(
                player_url, player_page, video_id, m3u8_id='hls-%s' % kind,
                m3u8_entry_protocol='m3u8_native',
                preference=2 if 'hq' in kind else 1)
            formats.extend(entries[0]['formats'])

        self._sort_formats(formats)

        post_content = get_element_by_class('post-content', webpage)
        tags = re.findall(
            r'<li[^>]+class="tag-[^"]+"><a[^>]*>([^<]+)</a></li>', post_content
        ) if post_content else None

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'tags': tags,
        }
