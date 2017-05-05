# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VideoIUAIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?video\.i\.ua/(user|channel)/((?P<user>[0-9]+)/(?P<folder>[0-9]+)|(?P<channel>[0-9]+))/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://video.i.ua/channel/528/405379/',
        'md5': 'c641d67f0b242f3ef8eebe683dbbce22',
        'info_dict': {
            'id': '405379',
            'ext': 'mp4',
            'title': 'Airbats 801 TTS 03 of 07',
            'thumbnail': r're:^https?://.*\.jpg$'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<div\s+class="post_title">\s*<h2>(.+?)</h2>', webpage, 'title')
        self.report_extraction(video_id)
        video_url = self._html_search_regex(r'<video\s*id="video"\s*src="(.+?)"', webpage, u'video URL')
        thumb_url = self._html_search_regex(r"poster:\s*'(.+?)'", webpage, u'thumbnail URL')
        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'mp4',
            'thumbnail': thumb_url
        }
