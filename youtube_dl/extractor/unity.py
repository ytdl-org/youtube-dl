from __future__ import unicode_literals

from .common import InfoExtractor
from .youtube import YoutubeIE


class UnityIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?unity3d\.com/learn/tutorials/(?:.*)/(?P<id>[0-9a-zA-Z-]+)'
    _TESTS = [{
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
    }, {
        'url': 'https://unity3d.com/learn/tutorials/projects/2d-ufo-tutorial/following-player-camera?playlist=25844',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        vid = self._match_id(url)
        webpage = self._download_webpage(url, vid)
        youtube_id = self._search_regex(
            r'data-video-id="([_0-9a-zA-Z-]+)"',
            webpage, 'youtube ID')
        return self.url_result(youtube_id, video_id=vid, ie=YoutubeIE.ie_key())
