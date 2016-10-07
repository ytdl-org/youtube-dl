# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import determine_ext


class YuvutuIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?yuvutu.com/video/(?P<id>[0-9]+)(?:.*)'
    _TEST = {
        'url': 'http://www.yuvutu.com/video/330/',
        'md5': 'af4a0d2eabec6b6bd43cd6b68543fa9c',
        'info_dict': {
            'id': '330',
            'title': 'carnal bliss',
            'ext': 'flv',
            'age_limit': 18,
        }
    }

    _title_regex = r"class=[\"']video-title-content[\"']>.+?>(.+?)<"
    _thumbnail_regex = r"itemprop=[\"']thumbnailURL[\"']\s+content=[\"'](.+?)[\"']"
    _embed_regex = r"[\"'](\/embed_video\.php.+?)[\"']"
    _video_regex = r"file:\s*[\"']([^\s]+)[\"']"

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(self._title_regex, webpage, 'title')

        embed_url = self._html_search_regex(self._embed_regex, webpage,
                                            'embed')
        embed_webpage = self._download_webpage(
            "http://www.yuvutu.com/" + embed_url, video_id)
        video_url = self._html_search_regex(self._video_regex, embed_webpage,
                                            'video_url')

        return {
            'id': video_id,
            'url': video_url,
            'ext': determine_ext(video_url, 'mp4'),
            'title': title,
            'age_limit': 18,
        }
