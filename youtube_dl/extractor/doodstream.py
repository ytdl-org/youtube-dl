# coding: utf-8
from __future__ import unicode_literals

import random
import string
import time

from ..compat import compat_filter as filter
from ..utils import (
    clean_html,
    ExtractorError,
    get_element_by_class,
    parse_duration,
    parse_filesize,
    update_url_query,
    unified_strdate,
    url_or_none,
)

from .common import InfoExtractor


class DoodStreamIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dood\.(?:to|watch|so|la|pm|sh|ws|one)/[ed]/(?P<id>[a-z0-9]+)'
    _TESTS = [{
        'url': 'http://dood.to/e/5s1wmbdacezb',
        'md5': '4568b83b31e13242b3f1ff96c55f0595',
        'info_dict': {
            'id': '5s1wmbdacezb',
            'ext': 'mp4',
            'title': 'Kat Wonders - Monthly May 2020',
            'description': 'Kat Wonders - Monthly May 2020 | DoodStream.com',
            'thumbnail': 'https://img.doodcdn.com/snaps/flyus84qgl2fsk4g.jpg',
        },
        'skip': 'Video not found',
    }, {
        'url': 'http://dood.watch/d/5s1wmbdacezb',
        'md5': '4568b83b31e13242b3f1ff96c55f0595',
        'info_dict': {
            'id': '5s1wmbdacezb',
            'ext': 'mp4',
            'title': 'Kat Wonders - Monthly May 2020',
            'description': 'Kat Wonders - Monthly May 2020 | DoodStream.com',
            'thumbnail': 'https://img.doodcdn.com/snaps/flyus84qgl2fsk4g.jpg',
        },
        'skip': 'Video not found',
    }, {
        'url': 'https://dood.to/d/jzrxn12t2s7n',
        'md5': '3207e199426eca7c2aa23c2872e6728a',
        'info_dict': {
            'id': 'jzrxn12t2s7n',
            'ext': 'mp4',
            'title': 'Stacy Cruz Cute ALLWAYSWELL',
            'description': 'Stacy Cruz Cute ALLWAYSWELL | DoodStream.com',
            'thumbnail': 'https://img.doodcdn.com/snaps/8edqd5nppkac3x8u.jpg',
        },
        'skip': 'Video not found',
    }, {
        'url': 'https://dood.to/d/is34uy8wvaet',
        'md5': '04740d3ba93bcd638aa7a097d9226710',
        'info_dict': {
            'id': 'is34uy8wvaet',
            'ext': 'mp4',
            'title': 'Akhanda (2021) Telugu DVDScr MP3 700MB',
            'upload_date': '20211202',
            'thumbnail': r're:https?://img\.doodcdn\.com?/[\w/]+\.jpg',
            'filesize_approx': int,
            'duration': 9886,
        }
    }, {
        'url': 'https://dood.so/d/wlihoael8uog',
        'md5': '2c14444c89788cc309738c1560abe278',
        'info_dict': {
            'id': 'wlihoael8uog',
            'ext': 'mp4',
            'title': 'VID 20220319 161659',
            'thumbnail': r're:https?://img\.doodcdn\.com?/splash/rmpnhb8ckkk79cge\.jpg',
            'upload_date': '20220319',
            'filesize_approx': int,
            'duration': 12.0,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'https://dood.to/e/' + video_id
        headers = {
            'User-Agent': 'Mozilla/5.0',  # (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/66.0',
        }
        webpage = self._download_webpage(url, video_id, headers=headers)

        def get_title(html, fatal=False):
            return self._html_search_regex(r'<title\b[^>]*>([^<]+?)(?:[|-]\s+DoodStream\s*)?</title', html, 'title', fatal=fatal)

        title = get_title(webpage)
        if title == 'Video not found':
            raise ExtractorError(title, expected=True)
        token = self._html_search_regex(r'''[?&]token=([a-z0-9]+)[&']''', webpage, 'token')

        headers.update({
            # 'User-Agent': 'Mozilla/5.0',  # (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/66.0',
            'referer': url
        })

        pass_md5 = self._html_search_regex(r'(/pass_md5.*?)\'', webpage, 'pass_md5')
        final_url = (
            self._download_webpage('https://dood.to' + pass_md5, video_id, headers=headers, note='Downloading final URL')
            + ''.join((random.choice(string.ascii_letters + string.digits) for _ in range(10)))
        )
        final_url = update_url_query(final_url, {'token': token, 'expiry': int(time.time() * 1000), })

        thumb = next(filter(None, (url_or_none(self._html_search_meta(x, webpage, default=None))
                                   for x in ('og:image', 'twitter:image'))), None)
        description = self._html_search_meta(
            ('og:description', 'description', 'twitter:description'), webpage, default=None)

        webpage = self._download_webpage('https://dood.to/d/' + video_id, video_id, headers=headers, fatal=False) or ''

        title = (
            self._html_search_meta(('og:title', 'twitter:title'), webpage, default=None)
            or get_title(webpage, fatal=(title is not None))
            or title)

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
