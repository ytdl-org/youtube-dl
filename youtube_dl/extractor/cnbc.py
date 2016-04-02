# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import smuggle_url


class CNBCIE(InfoExtractor):
    _VALID_URL = r'https?://video\.cnbc\.com/gallery/\?video=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://video.cnbc.com/gallery/?video=3000503714',
        'info_dict': {
            'id': '3000503714',
            'ext': 'mp4',
            'title': 'Fighting zombies is big business',
            'description': 'md5:0c100d8e1a7947bd2feec9a5550e519e',
            'timestamp': 1459332000,
            'upload_date': '20160330',
            'uploader': 'NBCU-CNBC',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
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
