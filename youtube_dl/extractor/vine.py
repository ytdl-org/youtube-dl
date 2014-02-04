from __future__ import unicode_literals

import re

from .common import InfoExtractor


class VineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vine\.co/v/(?P<id>\w+)'
    _TEST = {
        'url': 'https://vine.co/v/b9KOOWX7HUx',
        'md5': '2f36fed6235b16da96ce9b4dc890940d',
        'info_dict': {
            'id': 'b9KOOWX7HUx',
            'ext': 'mp4',
            'uploader': 'Jack Dorsey',
            'title': 'Chicken.',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage_url = 'https://vine.co/v/' + video_id
        webpage = self._download_webpage(webpage_url, video_id)

        self.report_extraction(video_id)

        video_url = self._html_search_meta('twitter:player:stream', webpage,
            'video URL')

        uploader = self._html_search_regex(r'<p class="username">(.*?)</p>',
            webpage, 'uploader', fatal=False, flags=re.DOTALL)

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'uploader': uploader,
        }
