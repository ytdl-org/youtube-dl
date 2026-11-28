# coding: utf-8
from __future__ import unicode_literals

import string
import random
import time

from .common import InfoExtractor
from ..utils import (
    js_to_json,
    urljoin,
)


class DoodStreamIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:doodstream\.com|dood\.(?:la|so|to|watch))/[de]/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://dood.to/d/wpyp2mgwi2kb',
        'md5': '2aaf633bcd5fefb64b27344f55022bf9',
        'info_dict': {
            'id': 'wpyp2mgwi2kb',
            'ext': 'mp4',
            'title': 'Big Buck Bunny Trailer',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        url = urljoin(url, '/e/' + video_id)
        referer = {'Referer': url}
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<title>(.+?)\s+-\s+DoodStream</title>',
                                        webpage, 'title')
        thumbnail = self._html_search_regex(r"('https?://img\.doodcdn\.com/splash/.+?')",
                                            webpage, 'thumbnail')
        thumbnail = self._parse_json(thumbnail, video_id,
                                     transform_source=js_to_json)

        token = self._html_search_regex(r"[?&]token=([a-z0-9]+)[&']", webpage, 'token')
        auth_url = self._html_search_regex(r"('/pass_md5.*?')", webpage,
                                           'pass_md5')
        auth_url = self._parse_json(auth_url, video_id,
                                    transform_source=js_to_json)
        auth_url = urljoin(url, auth_url)

        webpage = self._download_webpage(auth_url, video_id, headers=referer)
        final_url = webpage + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10)) + '?token=' + token + '&expiry=' + str(int(time.time() * 1000))

        return {
            'id': video_id,
            'title': title,
            'url': final_url,
            'http_headers': referer,
            'ext': 'mp4',
            'thumbnail': thumbnail,
        }
