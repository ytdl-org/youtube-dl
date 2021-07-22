# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VOEIE(InfoExtractor):
    IE_NAME = 'voe'
    IE_DESC = 'VOE.SX'
    _VALID_URL = r'https?://voe\.sx/(e/)?(?P<id>[a-z0-9]+)'
    _TEST = {
        'url': 'https://voe.sx/e/ng7ja5n5n2y8',
        'info_dict': {
            'id': 'ng7ja5n5n2y8',
            'title': 'md5:05ab15eb43a32f0f5918755156c5fb34',
            'thumbnail': r're:^https?://.*\.jpg$',
            'ext': 'm3u8',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://voe.sx/e/%s' % video_id, video_id)

        m3u8 = self._search_regex(
            r'(https.+m3u8)',
            webpage, 'm3u8')

        title = self._search_regex(
            r'<title>Watch (?P<title>.+)<\/title>',
            webpage, 'title', group='title')

        thumbnail = self._search_regex(
            r'VOEPlayer.poster="(?P<thumbnail>https.+)"',
            webpage, 'thumbnail', group='thumbnail')

        formats = self._extract_m3u8_formats(m3u8, video_id)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
        }
