# coding: utf-8
from __future__ import unicode_literals

import random
import string
import time
import re

from ..utils import (
    clean_html,
    get_element_by_class,
    parse_duration,
    parse_filesize,
    unified_strdate,
)

from .common import InfoExtractor


class DoodStreamIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<host>(?:www\.)?(dood|ds2play)\.(?:[^/]*))/[ed]/(?P<id>[a-z0-9]+)'
    _TESTS = [{
        'url': 'https://dood.li/e/h7ecgw5oqn8k',
        'md5': '90f2af170551c17fc78bee7426890054',
        'info_dict': {
            'id': 'h7ecgw5oqn8k',
            'ext': 'mp4',
            'title': 'Free-Slow-Music - DoodStream',
            'thumbnail': 'https://img.doodcdn.co/splash/7mbnwydhb6kb7xyk.jpg',
        }
    }, {
        'url': 'http://dood.watch/d/h7ecgw5oqn8k',
        'md5': '90f2af170551c17fc78bee7426890054',
        'info_dict': {
            'id': 'h7ecgw5oqn8k',
            'ext': 'mp4',
            'title': 'Free-Slow-Music - DoodStream',
            'thumbnail': 'https://img.doodcdn.co/splash/7mbnwydhb6kb7xyk.jpg',
        }
    }, {
        'url': 'https://dood.li/d/wlihoael8uog',
        'md5': '2c14444c89788cc309738c1560abe278',
        'info_dict': {
            'id': 'wlihoael8uog',
            'ext': 'mp4',
            'title': 'VID 20220319 161659 - DoodStream',
            'thumbnail': 'https://img.doodcdn.co/splash/rmpnhb8ckkk79cge.jpg',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        host = re.match(self._VALID_URL, url).groups()[0]
        url = url.replace(host, 'dood.li')
        host = 'dood.li'
        webpage = self._download_webpage(url, video_id)

        if '/d/' in url:
            url = ('https://%s' % host) + self._html_search_regex(
                r'<iframe src="(/e/[a-z0-9]+)"', webpage, 'embed')
            video_id = self._match_id(url)
            webpage = self._download_webpage(url, video_id)

        title = self._html_search_meta(['og:title', 'twitter:title'],
                                       webpage, default=None) or self._html_search_regex(
            r'<title\b[^>]*>([^<]+)</title>', webpage, 'title', default=None)
        thumb = self._html_search_meta(['og:image', 'twitter:image', 'poster'],
                                       webpage, default=None)
        token = self._html_search_regex(r'[?&]token=([a-z0-9]+)[&\']', webpage, 'token')
        description = self._html_search_meta(
            ['og:description', 'description', 'twitter:description'],
            webpage, default=None)
        auth_url = ('https://%s/' % host) + self._html_search_regex(
            r'(/pass_md5.*?)\'', webpage, 'pass_md5')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/66.0',
            'Referer': url
        }
        authpage = self._download_webpage(auth_url, video_id, headers=headers)
        final_url = authpage + ''.join([random.choice(string.ascii_letters + string.digits) for _ in
                                       range(10)]) + "?token=" + token + "&expiry=" + str(int(time.time() * 1000))

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
