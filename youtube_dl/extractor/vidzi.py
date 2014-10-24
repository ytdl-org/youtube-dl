from __future__ import unicode_literals

from .common import InfoExtractor


class VidziIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vidzi\.tv/(?P<id>\w+)'
    _TEST = {
        'url': 'http://vidzi.tv/m1chxrwq7bx9',
        'md5': '5c4c4a8ca2281a199c8eefe8f411d630',
        'info_dict': {
            'id': 'm1chxrwq7bx9',
            'ext': 'mp4',
            'title': 'Watch Cadbury Dream Factory S01E04 HDTV x264 FiHTV mp4',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        
        webpage = self._download_webpage(url, video_id)
        video_url = self._html_search_regex(
            r'{\s*file\s*:\s*"([^"]+)"\s*}', webpage, 'video url')
        title = self._html_search_regex(
            r'<Title>([^<]+)<\/Title>', webpage, 'title')
        
        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'mp4',
        }
        