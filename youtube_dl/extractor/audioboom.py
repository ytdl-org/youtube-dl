# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import float_or_none


class AudioBoomIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?audioboom\.com/boos/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://audioboom.com/boos/4279833-3-09-2016-czaban-hour-3?t=0',
        'md5': '63a8d73a055c6ed0f1e51921a10a5a76',
        'info_dict': {
            'id': '4279833',
            'ext': 'mp3',
            'title': '3/09/2016 Czaban Hour 3',
            'description': 'Guest:   Nate Davis - NFL free agency,   Guest:   Stan Gans',
            'duration': 2245.72
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)

        download_url = self._og_search_property('audio', webpage, 'url')

        duration = float_or_none(self._html_search_meta(
            'weibo:audio:duration', webpage, fatal=False))

        return {
            'id': video_id,
            'title': title,
            'url': download_url,
            'description': self._og_search_description(webpage),
            'duration': duration,
        }
