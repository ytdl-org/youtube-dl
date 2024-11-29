# coding: utf-8
from __future__ import unicode_literals

from random import choice as random_choice
from string import ascii_letters, digits
from time import time as time_time

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
    # dood.* redirects
    # .watch -> .re (but HEAD request fails in GenericIE)
    # .so -> .li
    _VALID_URL = r'https?://(?:www\.)?(?P<host>dood\.(?:to|la|li|pm|re|sh|watch|ws|one)|ds2play\.com)/[ed]/(?P<id>[a-z\d]+)'
    _TESTS = [{
        'url': 'https://dood.li/e/h7ecgw5oqn8k',
        'md5': '90f2af170551c17fc78bee7426890054',
        'info_dict': {
            'id': 'h7ecgw5oqn8k',
            'ext': 'mp4',
            'title': 'Free-Slow-Music',
            'upload_date': '20230814',
            'thumbnail': 'https://img.doodcdn.co/splash/7mbnwydhb6kb7xyk.jpg',
        },
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
        },
        'skip': 'Video not found',
    }, {
        'url': 'https://dood.sh/d/wlihoael8uog',
        'md5': '2c14444c89788cc309738c1560abe278',
        'info_dict': {
            'id': 'wlihoael8uog',
            'ext': 'mp4',
            'title': 'VID 20220319 161659',
            'thumbnail': r're:https?://img\.doodcdn\.com?/splash/rmpnhb8ckkk79cge\.jpg',
            'upload_date': '20220319',
            'filesize_approx': int,
            'duration': 12.0,
        },
    }, {
        'url': 'http://dood.ws /d/h7ecgw5oqn8k',
        'only_matching': True,
    }, {
        'url': 'https://dood.li/d/wlihoael8uog',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        host = 'dood.li'
        url = 'https://%s/e/%s' % (host, video_id)
        webpage = self._download_webpage(url, video_id, note='Downloading "/e/" webpage')

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
        # construct the media link
        final_url = self._download_webpage(
            'https://%s/%s' % (host, pass_md5), video_id, headers={
                'Referer': url,
            }, note='Downloading authpage URL')
        final_url += ''.join((random_choice(ascii_letters + digits)
                                        for _ in range(10)))
        final_url = update_url_query(final_url, {
            'token': token,
            'expiry': int(time_time() * 1000),
        })

        thumb = next(filter(None, (url_or_none(self._html_search_meta(x, webpage, default=None))
                                   for x in ('og:image', 'twitter:image'))), None)
        description = self._html_search_meta(
            ('og:description', 'description', 'twitter:description'), webpage, default=None)

        webpage = self._download_webpage(
            'https://%s/d/%s' % (host, video_id), video_id, fatal=False,
            note='Downloading alternative "/d/" page') or ''

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
