from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class FreespeechIE(InfoExtractor):
    IE_NAME = 'freespeech.org'
    _VALID_URL = r'https?://(?:www\.)?freespeech\.org/video/(?P<title>.+)'
    _TEST = {
        'add_ie': ['Youtube'],
        'url': 'https://www.freespeech.org/video/obama-romney-campaign-colorado-ahead-debate-0',
        'info_dict': {
            'id': 'poKsVCZ64uU',
            'ext': 'webm',
            'title': 'Obama, Romney Campaign in Colorado Ahead of Debate',
            'description': 'Obama, Romney Campaign in Colorado Ahead of Debate',
            'uploader': 'freespeechtv',
            'uploader_id': 'freespeechtv',
            'upload_date': '20121002',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title = mobj.group('title')
        webpage = self._download_webpage(url, title)
        info_json = self._search_regex(r'jQuery.extend\(Drupal.settings, ({.*?})\);', webpage, 'info')
        info = json.loads(info_json)

        return {
            '_type': 'url',
            'url': info['jw_player']['basic_video_node_player']['file'],
            'ie_key': 'Youtube',
        }
