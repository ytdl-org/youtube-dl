# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class CheekyVideosIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cheekyvideos\.net/(?P<id>.*)\.html?$'
    _TEST = {
        'url': 'https://yourextractor.com/watch/42',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '42',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')
        video_url = self._html_search_regex(r'<video[^>]+.src="(videos/[^"]+)"', webpage, 'url')
        uploader = video_id.split('/')[0]
        video_id = video_id.split('/')[1]
        url = 'https://cheekyvideos.net/%s/%s' % (uploader, video_url)

        return {
            'id': video_id,
            'title': title,
            'description': self._html_search_meta('description', webpage, default=None),
            'uploader': uploader,
            'url': url,
        }
