from __future__ import unicode_literals

import re

from .common import InfoExtractor


class IconosquareIE(InfoExtractor):
    _VALID_URL = r'https?://(www\.)?(?:iconosquare\.com|statigr\.am)/p/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://statigr.am/p/522207370455279102_24101272',
        'md5': '6eb93b882a3ded7c378ee1d6884b1814',
        'info_dict': {
            'id': '522207370455279102_24101272',
            'ext': 'mp4',
            'uploader_id': 'aguynamedpatrick',
            'title': 'Instagram photo by @aguynamedpatrick (Patrick Janelle)',
            'description': 'md5:644406a9ec27457ed7aa7a9ebcd4ce3d',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        html_title = self._html_search_regex(
            r'<title>(.+?)</title>',
            webpage, 'title')
        title = re.sub(r'(?: *\(Videos?\))? \| (?:Iconosquare|Statigram)$', '', html_title)
        uploader_id = self._html_search_regex(
            r'@([^ ]+)', title, 'uploader name', fatal=False)

        return {
            'id': video_id,
            'url': self._og_search_video_url(webpage),
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'uploader_id': uploader_id
        }
