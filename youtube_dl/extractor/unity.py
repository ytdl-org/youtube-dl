from __future__ import unicode_literals

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError
)


class UnityIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?unity3d\.com/learn/tutorials/(?:.*)/(?P<id>[0-9a-zA-Z-]+)'
    _TEST = {
        'url': 'https://unity3d.com/learn/tutorials/topics/animation/animate-anything-mecanim',
        'info_dict': {
            'id': 'jWuNtik0C8E',
            'ext': 'mp4',
            'title': 'Live Training 22nd September 2014 -  Animate Anything',
            'description': 'md5:e54913114bd45a554c56cdde7669636e',
            'duration': 2893,
            'uploader': 'Unity',
            'uploader_id': 'Unity3D',
            'upload_date': '20140926',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        youtube_id = self._search_regex(
            r'data-video-id="([_0-9a-zA-Z-]+)"',
            webpage, 'youtube ID', default=None)
        if not youtube_id:
            raise ExtractorError('Unable to extract youtube ID', expected=True)
        youtube_url = 'https://youtu.be/%s' % youtube_id
        return self.url_result(youtube_url, ie=YoutubeIE.ie_key())
