# coding: utf-8
from __future__ import unicode_literals

from ..compat import compat_urlparse
from ..utils import urljoin
from .common import InfoExtractor


class PeertubeIE(InfoExtractor):
    IE_DESC = 'Peertube Videos'
    IE_NAME = 'Peertube'
    _VALID_URL = r'https?:\/\/peertube\.touhoppai\.moe\/videos\/watch\/(?P<id>[0-9|a-z]{8}-[0-9|a-z]{4}-[0-9|a-z]{4}-[0-9|a-z]{4}-[0-9|a-z]{12})'
    _TEST = {
        'url': 'https://peertube.touhoppai.moe/videos/watch/7f3421ae-6161-4a4a-ae38-d167aec51683',
        'md5': 'a5e1e4a978e6b789553198d1739f5643',
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
        base_url = "%s://%s" % (url_data.scheme, url_data.hostname)
        api_url = urljoin(urljoin(base_url, "/api/v1/videos/"), video_id)
        details = self._download_json(api_url, video_id)
        return {
            'id': video_id,
            'title': details.get('name'),
            'description': details.get('description'),
            'formats': [{'url': file_data['fileUrl'], 'filesize': file_data.get('size')} for file_data in sorted(details['files'], key=lambda x: x['size'])],
            'thumbnail': urljoin(base_url, details['thumbnailPath'])
        }
