# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import clean_html

class RTBFVideoIE(InfoExtractor):
    _VALID_URL = r'https?://www.rtbf.be/video/(?P<title>[^?]+)\?.*id=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.rtbf.be/video/detail_les-diables-au-coeur-episode-2?id=1921274',
        'md5': '799f334ddf2c0a582ba80c44655be570',
        'info_dict': {
            'id': '1921274',
            'ext': 'mp4',
            'title': 'Les Diables au coeur (épisode 2)',
            'duration': 3099,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        # TODO more code goes here, for example ...
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(
            r'<meta property="og:description" content="([^"]*)"',
            webpage, 'title', mobj.group('title'))

        iframe_url = self._html_search_regex(r'<iframe [^>]*src="([^"]+)"',
            webpage, 'iframe')
        iframe = self._download_webpage(iframe_url, video_id)

        data_video_idx = iframe.find('data-video')
        next_data_idx = iframe.find('data-', data_video_idx + 1)
        json_data_start = data_video_idx + len('data-video=') + 1
        json_data_end = next_data_idx - 2
        video_data = json.loads(clean_html(iframe[json_data_start:json_data_end]))

        return {
            'id': video_id,
            'title': title,
            'url': video_data['data']['downloadUrl'],
            'duration': video_data['data']['duration'],
        }
