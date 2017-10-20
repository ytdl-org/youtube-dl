from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    js_to_json,
)


class PornHdIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pornhd\.com/(?:[a-z]{2,4}/)?videos/(?P<id>\d+)(?:/(?P<display_id>.+))?'
    _TESTS = [{
        'url': 'http://www.pornhd.com/videos/9864/selfie-restroom-masturbation-fun-with-chubby-cutie-hd-porn-video',
        'md5': 'c8b964b1f0a4b5f7f28ae3a5c9f86ad5',
        'info_dict': {
            'id': '9864',
            'display_id': 'selfie-restroom-masturbation-fun-with-chubby-cutie-hd-porn-video',
            'ext': 'mp4',
            'title': 'Restroom selfie masturbation',
            'description': 'md5:3748420395e03e31ac96857a8f125b2b',
            'thumbnail': r're:^https?://.*\.jpg',
            'view_count': int,
            'age_limit': 18,
        }
    }, {
        # removed video
        'url': 'http://www.pornhd.com/videos/1962/sierra-day-gets-his-cum-all-over-herself-hd-porn-video',
        'md5': '956b8ca569f7f4d8ec563e2c41598441',
        'info_dict': {
            'id': '1962',
            'display_id': 'sierra-day-gets-his-cum-all-over-herself-hd-porn-video',
            'ext': 'mp4',
            'title': 'Sierra loves doing laundry',
            'description': 'md5:8ff0523848ac2b8f9b065ba781ccf294',
            'thumbnail': r're:^https?://.*\.jpg',
            'view_count': int,
            'age_limit': 18,
        },
        'skip': 'Not available anymore',
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id or video_id)

        title = self._html_search_regex(
            [r'<span[^>]+class=["\']video-name["\'][^>]*>([^<]+)',
             r'<title>(.+?) - .*?[Pp]ornHD.*?</title>'], webpage, 'title')

        sources = self._parse_json(js_to_json(self._search_regex(
            r"(?s)sources'?\s*[:=]\s*(\{.+?\})",
            webpage, 'sources', default='{}')), video_id)

        if not sources:
            message = self._html_search_regex(
                r'(?s)<(div|p)[^>]+class="no-video"[^>]*>(?P<value>.+?)</\1',
                webpage, 'error message', group='value')
            raise ExtractorError('%s said: %s' % (self.IE_NAME, message), expected=True)

        formats = []
        for format_id, video_url in sources.items():
            if not video_url:
                continue
            height = int_or_none(self._search_regex(
                r'^(\d+)[pP]', format_id, 'height', default=None))
            formats.append({
                'url': video_url,
                'format_id': format_id,
                'height': height,
            })
        self._sort_formats(formats)

        description = self._html_search_regex(
            r'<(div|p)[^>]+class="description"[^>]*>(?P<value>[^<]+)</\1',
            webpage, 'description', fatal=False, group='value')
        view_count = int_or_none(self._html_search_regex(
            r'(\d+) views\s*<', webpage, 'view count', fatal=False))
        thumbnail = self._search_regex(
            r"poster'?\s*:\s*([\"'])(?P<url>(?:(?!\1).)+)\1", webpage,
            'thumbnail', fatal=False, group='url')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'formats': formats,
            'age_limit': 18,
        }
