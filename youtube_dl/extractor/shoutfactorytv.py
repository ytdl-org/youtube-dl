# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_m3u8_attributes,
)


class ShoutFactoryTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?shoutfactorytv\.com/.*?/(?P<id>[0-9a-d]+)'
    _TEST = {
        'url': 'http://www.shoutfactorytv.com/mst3k-shorts/mst3k-short-x-marks-the-spot/57473979e0a6b40d7300809a',
        'md5': 'a04c5394947cead82be3808ec6285f71',
        'info_dict': {
            'id': '57473979e0a6b40d7300809a',
            'ext': 'mp4',
            'title': 'MST3K Short: X Marks The Spot',
            'series': 'MST3K Shorts',
            'description': 'Poor Joe gets grilled in a heavenly court in this WWII era film promoting road safety in New Jersey.',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<h2><span>(.+)</span>.+</h2>', webpage, 'title')
        series = self._html_search_regex(
            r'<h2><span>.+</span> (.+)</h2>', webpage, 'series', default=None)
		
        player_embed = re.search(
            r'<script src=(["\'])(?P<javascript>https://player.zype.com\S+)\1', webpage)
        if not player_embed:
            raise ExtractorError('Could not extract player\'s JavaScript.')
        javascript = player_embed.group('javascript')
        download_js = self._download_webpage(
            javascript, video_id, 'Downloading JavaScript page')
        
        m3u8 = self._html_search_regex(
            r"source0.src = '(.*?)'", download_js, 'm3u8')
        formats = self._extract_m3u8_formats(m3u8, video_id, 'mp4')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
			'series': series,
        }
