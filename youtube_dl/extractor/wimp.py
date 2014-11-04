from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .youtube import YoutubeIE


class WimpIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?wimp\.com/([^/]+)/'
    _TESTS = [{
        'url': 'http://www.wimp.com/maruexhausted/',
        'md5': 'f1acced123ecb28d9bb79f2479f2b6a1',
        'info_dict': {
            'id': 'maruexhausted',
            'ext': 'flv',
            'title': 'Maru is exhausted.',
            'description': 'md5:57e099e857c0a4ea312542b684a869b8',
        }
    }, {
        # youtube video
        'url': 'http://www.wimp.com/clowncar/',
        'info_dict': {
            'id': 'cG4CEr2aiSg',
            'ext': 'mp4',
            'title': 'Basset hound clown car...incredible!',
            'description': 'md5:8d228485e0719898c017203f900b3a35',
            'uploader': 'Gretchen Hoey',
            'uploader_id': 'gretchenandjeff1',
            'upload_date': '20140303',
        },
        'add_ie': ['Youtube'],
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        webpage = self._download_webpage(url, video_id)
        video_url = self._search_regex(
            r"[\"']file[\"']\s*[:,]\s*[\"'](.+?)[\"']", webpage, 'video URL')
        if YoutubeIE.suitable(video_url):
            self.to_screen('Found YouTube video')
            return {
                '_type': 'url',
                'url': video_url,
                'ie_key': YoutubeIE.ie_key(),
            }

        return {
            'id': video_id,
            'url': video_url,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
        }
