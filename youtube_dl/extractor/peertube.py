# coding: utf-8
from __future__ import unicode_literals

from ..compat import compat_urlparse
from .common import InfoExtractor


class PeertubeIE(InfoExtractor):
    IE_DESC = 'Peertube Videos'
    IE_NAME = 'Peertube'
    _VALID_URL = r'https?:\/\/peertube\.touhoppai\.moe\/videos\/watch\/(?P<id>[0-9|\-|a-z]+)'
    _TEST = {
        'url': 'https://peertube.touhoppai.moe/videos/watch/7f3421ae-6161-4a4a-ae38-d167aec51683',
        'md5': '051ef9823d237416d5a6fc0bd8d67812',
        'info_dict': {
            'id': '7f3421ae-6161-4a4a-ae38-d167aec51683',
            'ext': 'mp4',
            'title': 'David Revoy Live Stream: Speedpainting',
            'description': 'md5:4e67c2fec55739a2ccb86052505a741e',
            'thumbnail': 'https://peertube.touhoppai.moe/static/thumbnails/7f3421ae-6161-4a4a-ae38-d167aec51683.jpg',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url_data = compat_urlparse.urlparse(url)
        api_url = "%s://%s/api/v1/videos/%s" % (url_data.scheme, url_data.hostname, video_id)
        details = self._download_json(api_url, video_id)
        return {
            'id': video_id,
            'title': details['name'],
            'description': details['description'],
            'url': details['files'][-1]['fileUrl'],
            'thumbnail': url_data.scheme + '://' + url_data.hostname + details['thumbnailPath']
        }
