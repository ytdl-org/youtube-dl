from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    smuggle_url,
    url_basename
)


class AMCIE(InfoExtractor):
    IE_NAME = 'amc'
    _VALID_URL = r'https?://www\.amc\.com/.*?'
    _TESTS = [
        {
            'url': 'http://www.amc.com/shows/talking-bad/video-extras/episode-509-online-bonus-video-talking-bad',
            'md5': '0ee064a81e6043ae53d8d1fd8216a60f',
            'info_dict': {
                'id': 'JI4ZCEoT4cne',
                'ext': 'mp4',
                'title': 'Episode 509 Online Bonus Video: Talking Bad',
                'description': 'md5:b451732ab2bf70452a689e9024d81ba3',
                'timestamp': 1376324809,
                'upload_date': '20130812',
                'uploader': 'AMCN',
            },
            'add_ie': ['ThePlatform']
        }
    ]

    def _real_extract(self, url):
        name = url_basename(url)
        webpage = self._download_webpage(url, name)
        account_id = 'M_UwQC'
        video_id = self._search_regex(
            r"class='platform-container'[^>]+data-video-id='([^']+)'",
            webpage, 'video_id')

        return {
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'url': smuggle_url(
                'http://link.theplatform.com/s/%s/media/%s?mbr=true' % (account_id, video_id),
                {'force_smil_url': True}),
            'id': video_id
        }

