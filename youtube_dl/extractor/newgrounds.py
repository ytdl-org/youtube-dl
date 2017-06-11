from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class NewgroundsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?newgrounds\.com/(?:audio/listen|portal/view)/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://www.newgrounds.com/audio/listen/549479',
        'md5': 'fe6033d297591288fa1c1f780386f07a',
        'info_dict': {
            'id': '549479',
            'ext': 'mp3',
            'title': 'B7 - BusMode',
            'uploader': 'Burn7',
        }
    }, {
        'url': 'https://www.newgrounds.com/portal/view/673111',
        'md5': '3394735822aab2478c31b1004fe5e5bc',
        'info_dict': {
            'id': '673111',
            'ext': 'mp4',
            'title': 'Dancin',
            'uploader': 'Squirrelman82',
        },
    }, {
        # source format unavailable, additional mp4 formats
        'url': 'http://www.newgrounds.com/portal/view/689400',
        'info_dict': {
            'id': '689400',
            'ext': 'mp4',
            'title': 'ZTV News Episode 8',
            'uploader': 'BennettTheSage',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        media_id = self._match_id(url)

        webpage = self._download_webpage(url, media_id)

        title = self._html_search_regex(
            r'<title>([^>]+)</title>', webpage, 'title')

        video_url = self._parse_json(self._search_regex(
            r'"url"\s*:\s*("[^"]+"),', webpage, ''), media_id)

        formats = [{
            'url': video_url,
            'format_id': 'source',
            'quality': 1,
        }]

        max_resolution = int_or_none(self._search_regex(
            r'max_resolution["\']\s*:\s*(\d+)', webpage, 'max resolution',
            default=None))
        if max_resolution:
            url_base = video_url.rpartition('.')[0]
            for resolution in (360, 720, 1080):
                if resolution > max_resolution:
                    break
                formats.append({
                    'url': '%s.%dp.mp4' % (url_base, resolution),
                    'format_id': '%dp' % resolution,
                    'height': resolution,
                })

        self._check_formats(formats, media_id)
        self._sort_formats(formats)

        uploader = self._html_search_regex(
            r'(?:Author|Writer)\s*<a[^>]+>([^<]+)', webpage, 'uploader',
            fatal=False)

        return {
            'id': media_id,
            'title': title,
            'uploader': uploader,
            'formats': formats,
        }
