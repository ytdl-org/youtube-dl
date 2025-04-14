from __future__ import unicode_literals

import re

from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    str_to_int,
    url_or_none,
)
from .common import InfoExtractor
from ..aes import aes_decrypt_text
from ..compat import compat_urllib_parse_unquote


class Tube8IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tube8\.com/(?:[^/]+/)+(?P<display_id>[^/]+)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.tube8.com/erotic/playtime/81807731/',
        'md5': 'fefa69ff76debaa63aa59374bfc51c95',
        'info_dict': {
            'id': '81807731',
            'display_id': 'playtime',
            'ext': 'mp4',
            'uploader': 'kikkijay-ph',
            'title': 'Playtime',
            'age_limit': 18,
            'duration': 988,
            'categories': ['Erotic'],
            'tags': ['adult toys', 'big boobs', 'butt', 'masturbate'],
        },
    }]

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+\bsrc=["\']((?:https?:)?//(?:www\.)?tube8\.com/embed/(?:[^/]+/)+\d+)',
            webpage)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

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
            duration = int_or_none(flashvars.get('video_duration'))
            encrypted = flashvars.get('encrypted') is True
            uploader = flashvars.get('sponsor')
            for key, value in flashvars.items():
                mobj = re.search(r'quality_(\d+)[pP]', key)
                if mobj:
                    extract_format(value, int(mobj.group(1)))
            video_url = flashvars.get('video_url')
            for key, value in flashvars.items():
                mobj = re.search(r'quality_(\d+)[pP]', key)
                if mobj:
                    extract_format(value, int(mobj.group(1)))
            video_url = flashvars.get('video_url')
            if video_url and determine_ext(video_url, None):
                extract_format(video_url)

        video_url = self._html_search_regex(
            r'flashvars\.video_url\s*=\s*(["\'])(?P<url>http.+?)\1',
            webpage, 'video url', default=None, group='url')
        if video_url:
            extract_format(compat_urllib_parse_unquote(video_url))

        if not formats:
            if 'title="This video is no longer available"' in webpage:
                raise ExtractorError(
                    'Video %s is no longer available' % video_id, expected=True)

        self._sort_formats(formats)

        if not title:
            title = self._html_search_regex([
                r'<h1[^>]*>([^<]+)'
                r'videoTitle\s*=\s*"([^"]+)'], webpage, 'title', default=display_id.capitalize())

        like_count = int_or_none(self._search_regex(
            r'rupVar\s*=\s*(\d+);', webpage, 'like count', fatal=False))
        dislike_count = int_or_none(self._search_regex(
            r'rdownVar\s*=\s*(\d+);', webpage, 'dislike count', fatal=False))
        view_count = str_to_int(self._search_regex(
            r'Views:\s*</dt>\s*<dd>([\d,\.]+)',
            webpage, 'view count', fatal=False))
        comment_count = str_to_int(self._search_regex(
            r'<span id="allCommentsCount">\((\d+)\)</span>',
            webpage, 'comment count', fatal=False))

        category = self._search_regex(
            r'videoCategoryByName\s*=\s*"([^"]+)";',
            webpage, 'category', fatal=False)
        categories = [category] if category else None

        tags_str = self._search_regex(
            r"(?s)<li\s+class\s*=\s*'video-tag'\s+data-esp-node\s*=\s*'tag'>(.*?)</div>",
            webpage, 'tags', fatal=False)
        tags = [t for t in re.findall(
            r'<a[^>]+href=[^>]+>([^<]+)', tags_str)] if tags_str else None

        return {
            'uploader': uploader,
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': 18,
            'formats': formats,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': comment_count,
            'categories': categories,
            'tags': tags,
        }
