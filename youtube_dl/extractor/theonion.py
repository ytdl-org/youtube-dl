# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class TheOnionIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?theonion\.com/video/[^,]+,(?P<id>[0-9]+)/?'
    _TEST = {
        'url': 'http://www.theonion.com/video/man-wearing-mm-jacket-gods-image,36918/',
        'md5': '19eaa9a39cf9b9804d982e654dc791ee',
        'info_dict': {
            'id': '2133',
            'ext': 'mp4',
            'title': 'Man Wearing M&M Jacket Apparently Made In God\'s Image',
            'description': 'md5:cc12448686b5600baae9261d3e180910',
            'thumbnail': 're:^https?://.*\.jpg\?\d+$',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            r'"videoId":\s(\d+),', webpage, 'video ID')
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        sources = re.findall(r'<source src="([^"]+)" type="([^"]+)"', webpage)
        formats = []
        for src, type_ in sources:
            if type_ == 'video/mp4':
                formats.append({
                    'format_id': 'mp4_sd',
                    'preference': 1,
                    'url': src,
                })
            elif type_ == 'video/webm':
                formats.append({
                    'format_id': 'webm_sd',
                    'preference': 0,
                    'url': src,
                })
            elif type_ == 'application/x-mpegURL':
                formats.extend(
                    self._extract_m3u8_formats(src, display_id, preference=-1))
            else:
                self.report_warning(
                    'Encountered unexpected format: %s' % type_)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
        }
