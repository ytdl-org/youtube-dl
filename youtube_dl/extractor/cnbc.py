# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import smuggle_url


class CNBCIE(InfoExtractor):
    _VALID_URL = r'https?://video\.cnbc\.com/gallery/\?video=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://video.cnbc.com/gallery/?video=3000503714',
        'md5': '',
        'info_dict': {
            'id': '3000503714',
            'ext': 'mp4',
            'title': 'Video title goes here',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return {
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'url': smuggle_url(
                'http://link.theplatform.com/s/gZWlPC/media/guid/2408950221/%s?mbr=true&manifest=m3u' % video_id,
                {'force_smil_url': True}),
            'id': video_id,
        }
