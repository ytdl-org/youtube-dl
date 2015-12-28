# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VidziIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vidzi\.tv/(?P<id>\w+)'
    _TEST = {
        'url': 'http://vidzi.tv/cghql9yq6emu.html',
        'md5': '4f16c71ca0c8c8635ab6932b5f3f1660',
        'info_dict': {
            'id': 'cghql9yq6emu',
            'ext': 'mp4',
            'title': 'youtube-dl test video  1\\\\2\'3/4<5\\\\6ä7↭',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        video_host = self._html_search_regex(
            r'id=\'vplayer\'><img src="http://(.*?)/i', webpage,
            'video host')
        video_hash = self._html_search_regex(
            r'\|([a-z0-9]+)\|hls\|type', webpage, 'video_hash')
        ext = self._html_search_regex(
            r'\|tracks\|([a-z0-9]+)\|', webpage, 'video ext')
        video_url = 'http://' + video_host + '/' + video_hash + '/v.' + ext
        title = self._html_search_regex(
            r'(?s)<h2 class="video-title">(.*?)</h2>', webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
        }
