from __future__ import unicode_literals

import re

from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    str_to_int,
    strip_or_none,
    url_or_none,
)
from .common import InfoExtractor
from ..aes import aes_decrypt_text
from ..compat import compat_urllib_parse_unquote


class Tube8IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tube8\.com/(?:[^/]+/)+(?P<display_id>[^/]+)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.tube8.com/teen/kasia-music-video/229795/',
        'md5': '65e20c48e6abff62ed0c3965fff13a39',
        'info_dict': {
            'id': '229795',
            'display_id': 'kasia-music-video',
            'ext': 'mp4',
            'description': 'hot teen Kasia grinding',
            'uploader': 'unknown',
            'title': 'Kasia music video',
            'age_limit': 18,
            'duration': 230,
            'categories': ['Teen'],
            'tags': ['dancing'],
        },
    }, {
        'url': 'http://www.tube8.com/shemale/teen/blonde-cd-gets-kidnapped-by-two-blacks-and-punished-for-being-a-slutty-girl/19569151/',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+\bsrc=["\']((?:https?:)?//(?:www\.)?tube8\.com/embed/(?:[^/]+/)+\d+)',
            webpage)

    def _extract_info(self, url, fatal=True):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = (mobj.group('display_id')
                      if 'display_id' in mobj.groupdict()
                      else None) or mobj.group('id')

        webpage = self._download_webpage(
            url, display_id, headers={'Cookie': 'age_verified=1'})

        formats = []
        format_urls = set()

        title = None
        thumbnail = None
        duration = None
        encrypted = False

        def extract_format(format_url, height=None):
            format_url = url_or_none(format_url)
            if not format_url or not format_url.startswith(('http', '//')):
                return
            if format_url in format_urls:
                return
            format_urls.add(format_url)
            tbr = int_or_none(self._search_regex(
                r'[/_](\d+)[kK][/_]', format_url, 'tbr', default=None))
            if not height:
                height = int_or_none(self._search_regex(
                    r'[/_](\d+)[pP][/_]', format_url, 'height', default=None))
            if encrypted:
                format_url = aes_decrypt_text(
                    video_url, title, 32).decode('utf-8')
            formats.append({
                'url': format_url,
                'format_id': '%dp' % height if height else None,
                'height': height,
                'tbr': tbr,
            })

        flashvars = self._parse_json(
            self._search_regex(
                r'flashvars\s*=\s*({.+?});', webpage,
                'flashvars', default='{}'),
            display_id, fatal=False)

        if flashvars:
            title = flashvars.get('video_title')
            thumbnail = flashvars.get('image_url')

    def _real_extract(self, url):
        webpage, info = self._extract_info(url)

        if not info['title']:
            info['title'] = self._html_search_regex(
                r'videoTitle\s*=\s*"([^"]+)', webpage, 'title')

        description = self._html_search_regex(
            r'(?s)Description:</dt>\s*<dd>(.+?)</dd>', webpage, 'description', fatal=False)
        uploader = self._html_search_regex(
            r'<span class="username">\s*(.+?)\s*<',
            webpage, 'uploader', fatal=False)

        like_count = int_or_none(self._search_regex(
            r'rupVar\s*=\s*"(\d+)"', webpage, 'like count', fatal=False))
        dislike_count = int_or_none(self._search_regex(
            r'rdownVar\s*=\s*"(\d+)"', webpage, 'dislike count', fatal=False))
        view_count = str_to_int(self._search_regex(
            r'Views:\s*</dt>\s*<dd>([\d,\.]+)',
            webpage, 'view count', fatal=False))
        comment_count = str_to_int(self._search_regex(
            r'<span id="allCommentsCount">(\d+)</span>',
            webpage, 'comment count', fatal=False))

        category = self._search_regex(
            r'Category:\s*</dt>\s*<dd>\s*<a[^>]+href=[^>]+>([^<]+)',
            webpage, 'category', fatal=False)
        categories = [category] if category else None

        tags_str = self._search_regex(
            r'(?s)Tags:\s*</dt>\s*<dd>(.+?)</(?!a)',
            webpage, 'tags', fatal=False)
        tags = [t for t in re.findall(
            r'<a[^>]+href=[^>]+>([^<]+)', tags_str)] if tags_str else None

        info.update({
            'description': description,
            'uploader': uploader,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': comment_count,
            'categories': categories,
            'tags': tags,
        })

        return info
