# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    remove_end,
    remove_start
)


class PinkbikeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pinkbike\.com/video/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.pinkbike.com/video/402811/',
        'md5': '4814b8ca7651034cd87e3361d5c2155a',
        'info_dict': {
            'id': '402811',
            'ext': 'mp4',
            'title': 'Brandon Semenuk - RAW 100',
            'thumbnail': 're:^https?://.*\.jpg$',
            'location': 'Victoria, British Columbia, Canada',
            'uploader_id': 'revelco',
            'upload_date': '20150406',
            'description': 'Official release: www.redbull.ca/rupertwalker',
            'duration': 100
        }
    }, {
        'url': 'http://www.pinkbike.com/video/406629/',
        'md5': 'c7a3e19a2bd5cde5a1cda6b2b46caa74',
        'info_dict': {
            'id': '406629',
            'ext': 'mp4',
            'title': 'Chromag: Reece Wallace in Utah',
            'thumbnail': 're:^https?://.*\.jpg$',
            'location': 'Whistler, British Columbia, Canada',
            'uploader_id': 'Chromagbikes',
            'upload_date': '20150505',
            'description': 'Reece Wallace shredding Virgin, Utah. Video by Virtu Media.',
            'duration': 180
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')
        title = remove_end(title, ' Video - Pinkbike')

        description = self._html_search_meta('description', webpage, 'description')
        description = remove_start(description, title + '. ')

        duration = int_or_none(self._html_search_meta(
            'video:duration', webpage, 'duration'))

        uploader_id = self._html_search_regex(r'un:\s*"(.*?)"', webpage, 'uploader_id')

        upload_date = self._html_search_regex(
            r'class="fullTime"\s*title="([0-9]{4}(?:-[0-9]{2}){2})"',
            webpage, 'upload_date')
        upload_date = upload_date.replace('-', '')

        location = self._html_search_regex(
            r'<dt>Location</dt>\n?\s*<dd>\n?(.*?)\s*<img',
            webpage, 'location')

        formats = re.findall(
            r'<source data-quality=\\"([0-9]+)p\\" src=\\"(.*?)\\">',
            webpage)

        formats = [{'url': fmt[1], 'height': int_or_none(fmt[0])} for fmt in formats]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'thumbnail': self._html_search_meta('og:image', webpage, 'thumbnail'),
            'uploader_id': uploader_id,
            'upload_date': upload_date,
            'location': location,
            'formats': formats
        }
