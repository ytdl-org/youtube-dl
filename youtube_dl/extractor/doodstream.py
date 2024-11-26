# coding: utf-8
from __future__ import unicode_literals

import random
import string
import time

from ..utils import (
    clean_html,
    get_element_by_class,
    parse_duration,
    parse_filesize,
    unified_strdate,
)

from .common import (
    InfoExtractor,
    update_url_query,
)


class DoodStreamIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:dood\.(?:to|la|li|pm|re|sh|ws|one|watch)|ds2play\.com)/[ed]/(?P<id>[a-z0-9]+)'
    _TESTS = [{
        'url': 'https://dood.li/e/h7ecgw5oqn8k',
        'md5': '90f2af170551c17fc78bee7426890054',
        'info_dict': {
            'id': 'h7ecgw5oqn8k',
            'ext': 'mp4',
            'title': 'Free-Slow-Music',
            'thumbnail': 'https://img.doodcdn.co/splash/7mbnwydhb6kb7xyk.jpg',
        }
    }, {
        'url': 'http://dood.watch/d/h7ecgw5oqn8k',
        'only_matching': True,
    }, {
        'url': 'https://dood.li/d/wlihoael8uog',
        'md5': '2c14444c89788cc309738c1560abe278',
        'info_dict': {
            'id': 'wlihoael8uog',
            'ext': 'mp4',
            'title': 'VID 20220319 161659',
            'thumbnail': 'https://img.doodcdn.co/splash/rmpnhb8ckkk79cge.jpg',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        host = 'dood.li'
        url = 'https://%s/e/%s' % (host, video_id)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_meta(['og:title', 'twitter:title'],
                                       webpage, default=None) or self._html_search_regex(r'<title\b[^>]*>([^<]+?)(?:[|-]\s+DoodStream\s*)?</title', webpage, 'title', fatal=False)
        thumb = self._html_search_meta(['og:image', 'twitter:image', 'poster'],
                                       webpage, default=None)
        pass_md5, token = self._search_regex(
            r'["\']/(?P<pm>pass_md5/[\da-f-]+/(?P<tok>[\da-z]+))', webpage, 'tokens',
            group=('pm', 'tok'))

        auth_url = ('https://%s/' % host) + pass_md5
        headers = {'Referer': url}
        authpage = self._download_webpage(auth_url, video_id, headers=headers)
        final_url = update_url_query(
            authpage + ''.join((random.choice(string.ascii_letters + string.digits) for _ in range(10))),
            {
                'token': token,
                'expiry': int(time.time() * 1000),
            }
        )
        description = self._html_search_meta(
            ['og:description', 'description', 'twitter:description'],
            webpage, default=None)

        def get_class_text(x):
            return clean_html(get_element_by_class(x, webpage))

        return {
            'id': video_id,
            'title': title,
            'url': final_url,
            'http_headers': headers,
            'ext': 'mp4',
            'upload_date': unified_strdate(get_class_text('uploadate')),
            'duration': parse_duration(get_class_text('length')),
            'filesize_approx': parse_filesize(get_class_text('size')),
            'description': description,
            'thumbnail': thumb,
        }
