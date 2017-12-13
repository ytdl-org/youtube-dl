# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class InternazionaleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?internazionale\.it/video/(?P<id>.*)'
    _TESTS = [{
        'url': 'https://www.internazionale.it/video/2015/02/19/richard-linklater-racconta-una-scena-di-boyhood',
        'md5': '11b54a3d3333e455c00684e50a65c58e',
        'info_dict': {
            'id': '265968',
            'ext': 'mp4',
            'description': 'md5:efb7e5bbfb1a54ae2ed5a4a015f0e665',
            'title': 'Richard Linklater racconta una scena di Boyhood',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        data_job_id = self._html_search_regex(r'data-job-id="([^"]+)"', webpage, 'data-job-id')
        data_video_path = self._html_search_regex(r'data-video-path="([^"]+)"', webpage, 'data-video-path')

        formats = []

        formats.extend(self._extract_m3u8_formats(
            'https://video.internazionale.it/%s/%s.m3u8' % (data_video_path, data_job_id),
            video_id))

        formats.extend(self._extract_mpd_formats(
            'https://video.internazionale.it/%s/%s.mpd' % (data_video_path, data_job_id),
            video_id))

        self._sort_formats(formats)

        return {
            'id': data_job_id,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
            'formats': formats,
        }
