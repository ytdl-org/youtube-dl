# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

class PearIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pearvideo\.com/video_(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.pearvideo.com/video_1076290',
        'info_dict': {
            'id': '1076290',
            'ext': 'mp4',
            'title': '小浣熊在主人家玻璃上滚石头：没砸',
            'description': '小浣熊找到一个小石头，仿佛发现了一个宝贝。它不停地用石头按在玻璃上，滚来滚去，吸引主人注意。',
            'url': 'http://video.pearvideo.com/mp4/short/20170508/cont-1076290-10438018-hd.mp4'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1[^>]+class="video-tt">(.+)</h1>', webpage, 'title')
        description = self._html_search_regex(r'<div[^>]+class="summary"[^>]*>([^<]+)<', webpage, 'description', fatal=False)
        hdUrl = self._html_search_regex(r'hdUrl="(.*?)"', webpage, 'url')

        return {
            'id': video_id,
            'ext': 'mp4',
            'title': title,
            'description': description,
            'url': hdUrl
        }