# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VideoIUAIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?video\.i\.ua/user/(?P<user>[0-9]+)/(?P<folder>[0-9]+)/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://video.i.ua/user/3698736/77516/459718/',
        'md5': '7a9b4483dece501b69ac772156d85ce6',
        'info_dict': {
            'id': '459718',
            'ext': 'mp4',
            'title': u'Красавица на качелях...',
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
