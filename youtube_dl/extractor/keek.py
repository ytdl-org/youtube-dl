from __future__ import unicode_literals

import re

from .common import InfoExtractor


class KeekIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?keek\.com/(?:!|\w+/keeks/)(?P<videoID>\w+)'
    IE_NAME = 'keek'
    _TEST = {
        'url': 'https://www.keek.com/ytdl/keeks/NODfbab',
        'file': 'NODfbab.mp4',
        'md5': '9b0636f8c0f7614afa4ea5e4c6e57e83',
        'info_dict': {
            'uploader': 'ytdl',
            'title': 'test chars: "\'/\\\u00e4<>This is a test video for youtube-dl.For more information, contact phihag@phihag.de .',
        },
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        video_url = 'http://cdn.keek.com/keek/video/%s' % video_id
        thumbnail = 'http://cdn.keek.com/keek/thumbnail/%s/w100/h75' % video_id
        webpage = self._download_webpage(url, video_id)

        uploader = self._html_search_regex(
            r'<div class="user-name-and-bio">[\S\s]+?<h2>(?P<uploader>.+?)</h2>',
            webpage, 'uploader', fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': self._og_search_title(webpage),
            'thumbnail': thumbnail,
            'uploader': uploader
        }
