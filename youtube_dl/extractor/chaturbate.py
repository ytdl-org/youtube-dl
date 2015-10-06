# encoding: utf-8

from .common import InfoExtractor


class ChaturbateIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?chaturbate\.com/(?P<id>[^/]+)/?$'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        m3u8_url = self._search_regex(r"'(https?://.*?\.m3u8)'", webpage, 'playlist')

        formats = self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4')

        return {
            'id': video_id,
            'title': self._live_title(video_id),
            'description': self._html_search_meta('description', webpage, 'description'),
            'is_live': True,
            'thumbnail': 'https://cdn-s.highwebmedia.com/uHK3McUtGCG3SMFcd4ZJsRv8/roomimage/%s.jpg' % (video_id,),
            'formats': formats,
        }
