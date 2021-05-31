# coding: utf-8
from __future__ import unicode_literals

import string
import random
import time

from .common import InfoExtractor
from ..utils import (
    js_to_json,
    urljoin,
    try_get,
)


def doodExe(crp, crs):
    if crp == 'N_crp':
        return crs
    sorted_crp = ''.join(sorted(crp))
    result = ''
    for c in crs:
        i = crp.find(c)
        if i >= 0:
            result += sorted_crp[i]
    result = result.replace('+.+', '(')
    result = result.replace('+..+', ')')
    result = result.replace('+-+', '[')
    result = result.replace('+--+', ']')
    result = result.replace('+', ' ')
    return result


def try_doodExe(metadata, key):
    try:
        x = metadata[key]
        # everything that can go wrong in this call raises a TypeError
        return doodExe(**x)
    except (KeyError, TypeError):
        return None


class DoodStreamIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:doodstream\.com|dood\.(?:cx|so|to|watch))/[de]/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://dood.to/d/wpyp2mgwi2kb',
        'md5': '2aaf633bcd5fefb64b27344f55022bf9',
        'info_dict': {
            'id': 'wpyp2mgwi2kb',
            'ext': 'mp4',
            'title': 'Big Buck Bunny Trailer',
            'thumbnail': r're:^https?://.*\.jpg$',
            'filesize': 4447915,
            'duration': 33,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        url = urljoin(url, '/e/' + video_id)
        referer = {'Referer': url}
        webpage = self._download_webpage(url, video_id)

        metadata_url = self._html_search_regex(r"('/cptr/[^']*')", webpage,
                                               'video metadata')
        metadata_url = self._parse_json(metadata_url, video_id,
                                        transform_source=js_to_json)
        metadata_url = urljoin(url, metadata_url)
        metadata = self._download_json(metadata_url, video_id, headers=referer)

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
            'title': try_doodExe(metadata, 'ttl') or video_id,
            'url': final_url,
            'http_headers': referer,
            'ext': 'mp4',
            'thumbnail': self._og_search_thumbnail(webpage),
            'filesize': try_get(try_doodExe(metadata, 'siz'), lambda x: int(x, 10)),
            'duration': try_get(try_doodExe(metadata, 'len'), lambda x: int(x, 10)),
        }
