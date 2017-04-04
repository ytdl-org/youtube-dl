# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class StreamangoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?streamango\.com/(?:f|embed)/(?P<id>.+?)/(?:.+)'
    _TESTS = [{
        'url': 'https://streamango.com/f/clapasobsptpkdfe/20170315_150006_mp4',
        'md5': 'e992787515a182f55e38fc97588d802a',
        'info_dict': {
            'id': 'clapasobsptpkdfe',
            'ext': 'mp4',
            'title': '20170315_150006.mp4',
            'url': r're:https://streamango\.com/v/d/clapasobsptpkdfe~[0-9]{10}~(?:[0-9]+\.){3}[0-9]+~.{8}/720',
        }
    }, {
        'url': 'https://streamango.com/embed/clapasobsptpkdfe/20170315_150006_mp4',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        def extract_url(urltype):
            return self._search_regex(
                r'type\s*:\s*["\']{}["\']\s*,\s*src\s*:\s*["\'](?P<url>.+?)["\'].*'.format(urltype),
                webpage, 'video URL', group='url')

        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        url = 'https:' + extract_url('video/mp4')
        dashurl = extract_url(r'application/dash\+xml')

        formats = [{
            'url': url,
            'ext': 'mp4',
            'width': 1280,
            'height': 720,
            'format_id': 'mp4',
        }]

        formats.extend(self._extract_mpd_formats(
            dashurl, video_id, mpd_id='dash', fatal=False))

        self._sort_formats(formats)

        return {
            'id': video_id,
            'url': url,
            'title': title,
            'formats': formats,
        }
