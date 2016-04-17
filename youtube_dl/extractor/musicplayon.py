# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    int_or_none,
    js_to_json,
    mimetype2ext,
)


class MusicPlayOnIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?musicplayon\.com/play(?:-touch)?\?(?:v|pl=\d+&play)=(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://en.musicplayon.com/play?v=433377',
        'md5': '00cdcdea1726abdf500d1e7fd6dd59bb',
        'info_dict': {
            'id': '433377',
            'ext': 'mp4',
            'title': 'Rick Ross - Interview On Chelsea Lately (2014)',
            'description': 'Rick Ross Interview On Chelsea Lately',
            'duration': 342,
            'uploader': 'ultrafish',
        },
    }, {
        'url': 'http://en.musicplayon.com/play?pl=102&play=442629',
        'only_matching': True,
    }]

    _URL_TEMPLATE = 'http://en.musicplayon.com/play?v=%s'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = self._URL_TEMPLATE % video_id

        page = self._download_webpage(url, video_id)

        title = self._og_search_title(page)
        description = self._og_search_description(page)
        thumbnail = self._og_search_thumbnail(page)
        duration = self._html_search_meta('video:duration', page, 'duration', fatal=False)
        view_count = self._og_search_property('count', page, fatal=False)
        uploader = self._html_search_regex(
            r'<div>by&nbsp;<a href="[^"]+" class="purple">([^<]+)</a></div>', page, 'uploader', fatal=False)

        sources = self._parse_json(
            self._search_regex(r'setup\[\'_sources\'\]\s*=\s*([^;]+);', page, 'video sources'),
            video_id, transform_source=js_to_json)
        formats = [{
            'url': compat_urlparse.urljoin(url, source['src']),
            'ext': mimetype2ext(source.get('type')),
            'format_note': source.get('data-res'),
        } for source in sources]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'duration': int_or_none(duration),
            'view_count': int_or_none(view_count),
            'formats': formats,
        }
