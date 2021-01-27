from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    parse_duration,
    parse_filesize,
    int_or_none,
)


class AlphaPornoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?alphaporno\.com/videos/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://www.alphaporno.com/videos/sensual-striptease-porn-with-samantha-alexandra/',
        'md5': 'feb6d3bba8848cd54467a87ad34bd38e',
        'info_dict': {
            'id': '258807',
            'display_id': 'sensual-striptease-porn-with-samantha-alexandra',
            'ext': 'mp4',
            'title': 'Sensual striptease porn with Samantha Alexandra',
            'thumbnail': r're:https?://.*\.jpg$',
            'timestamp': 1418701811,
            'upload_date': '20141216',
            'duration': 387,
            'tbr': 1145,
            'categories': list,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            [r"video_id\s*:\s*'([^']+)'", r"\['video_id'\]\s*=\s*(.+?);"], webpage, 'video id')

        entries = self._parse_html5_media_entries('https://alphaporno.com', webpage, video_id)
        info = {}
        if len(entries) > 0:
            info = entries[0]
            for fmt in info['formats']:
                fmt['tbr'] = int_or_none(self._search_regex(r"br=(\d+)", fmt['url'], 'bitrate', default=None))
        else:
            video_url = self._search_regex(
                r"video_url\s*:\s*'([^']+)'", webpage, 'video url')
            ext = self._html_search_meta(
                'encodingFormat', webpage, 'ext', default='.mp4')[1:]
            bitrate = int_or_none(self._html_search_meta(
                'bitrate', webpage, 'bitrate', default=None))
            info = {
                'url': video_url,
                'ext': ext,
                'tbr': bitrate,
            }

        title = self._search_regex(
            [r'<meta content="([^"]+)" itemprop="description">',
             r'class="title" itemprop="name">([^<]+)<',
             r'<h1>(.*?)</h1>'],
            webpage, 'title')
        thumbnail = self._html_search_meta(['og:image', 'thumbnail'], webpage, 'thumbnail')
        timestamp = parse_iso8601(self._og_search_property('video:release_date', webpage, 'upload date', fatal=False),
                                  delimiter=' ') or parse_iso8601(self._html_search_meta('uploadDate', webpage, 'upload date'))
        duration = parse_duration(self._html_search_meta(
            ['duration', 'og:video:duration'], webpage, 'duration'))
        filesize_approx = parse_filesize(self._html_search_meta(
            'contentSize', webpage, 'file size', default=None))
        categories = self._html_search_meta(
            'keywords', webpage, 'categories', default='').split(',')

        age_limit = self._rta_search(webpage)

        info.update({
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'filesize_approx': filesize_approx,
            'categories': categories,
            'age_limit': age_limit,
        })
        return info
