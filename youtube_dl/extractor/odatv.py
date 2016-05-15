# coding: utf-8

from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    remove_start
)
import re


class OdaTVIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?odatv\.com/(?:mob|vid)_video\.php\?id=(?P<id>[^&]*)'
    _TESTS = [{
        'url': 'http://odatv.com/vid_video.php?id=8E388',
        'md5': 'dc61d052f205c9bf2da3545691485154',
        'info_dict': {
            'id': '8E388',
            'ext': 'mp4',
            'title': 'md5:69654805a16a16cf9ec9d055e079831c'
        }
    }, {
        'url': 'http://odatv.com/mob_video.php?id=8E388',
        'md5': 'dc61d052f205c9bf2da3545691485154',
        'info_dict': {
            'id': '8E388',
            'ext': 'mp4',
            'title': 'md5:69654805a16a16cf9ec9d055e079831c'
        }
    }, {
        'url': 'http://odatv.com/mob_video.php?id=8E900',
        'md5': '',
        'info_dict': {
            'id': '8E900',
            'ext': 'mp4',
            'title': 'not found check'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        if 'NO VIDEO!' in webpage:
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)

        return {
            'id': video_id,
            'title': remove_start(self._og_search_title(webpage), 'Video: '),
            'thumbnail': self._og_search_thumbnail(webpage),
            'url': self._html_search_regex(r"(http.+?video_%s\.mp4)" % re.escape(video_id), webpage, 'url', flags=re.IGNORECASE)
        }
