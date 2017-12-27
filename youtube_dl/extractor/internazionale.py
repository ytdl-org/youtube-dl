# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import unified_timestamp


class InternazionaleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?internazionale\.it/video/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://www.internazionale.it/video/2015/02/19/richard-linklater-racconta-una-scena-di-boyhood',
        'md5': '3e39d32b66882c1218e305acbf8348ca',
        'info_dict': {
            'id': '265968',
            'display_id': 'richard-linklater-racconta-una-scena-di-boyhood',
            'ext': 'mp4',
            'title': 'Richard Linklater racconta una scena di Boyhood',
            'description': 'md5:efb7e5bbfb1a54ae2ed5a4a015f0e665',
            'timestamp': 1424354635,
            'upload_date': '20150219',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'format': 'bestvideo',
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        DATA_RE = r'data-%s=(["\'])(?P<value>(?:(?!\1).)+)\1'

        title = self._search_regex(
            DATA_RE % 'video-title', webpage, 'title', default=None,
            group='value') or self._og_search_title(webpage)

        video_id = self._search_regex(
            DATA_RE % 'job-id', webpage, 'video id', group='value')
        video_path = self._search_regex(
            DATA_RE % 'video-path', webpage, 'video path', group='value')

        video_base = 'https://video.internazionale.it/%s/%s.' % (video_path, video_id)

        formats = self._extract_m3u8_formats(
            video_base + 'm3u8', display_id, 'mp4',
            entry_protocol='m3u8_native', m3u8_id='hls', fatal=False)
        formats.extend(self._extract_mpd_formats(
            video_base + 'mpd', display_id, mpd_id='dash', fatal=False))
        self._sort_formats(formats)

        timestamp = unified_timestamp(self._html_search_meta(
            'article:published_time', webpage, 'timestamp'))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
            'timestamp': timestamp,
            'formats': formats,
        }
