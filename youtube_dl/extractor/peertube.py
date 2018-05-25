# coding: utf-8
from __future__ import unicode_literals

from ..compat import compat_urlparse, compat_str
from ..utils import urljoin, int_or_none, try_get
from .common import InfoExtractor


class PeertubeIE(InfoExtractor):
    IE_DESC = 'Peertube Videos'
    IE_NAME = 'Peertube'
    _VALID_URL = r'(?:https?:)//peertube\.touhoppai\.moe\/videos\/watch\/(?P<id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
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
        base_url = "%s://%s" % (url_data.scheme or 'http', url_data.hostname)
        api_url = urljoin(base_url, "/api/v1/videos/%s" % video_id)
        details = self._download_json(api_url, video_id)
        formats = [{'url': file_data['fileUrl'], 'filesize': int_or_none(file_data.get('size')), 'format': file_data.get('resolution', {}).get('label')} for file_data in details['files']]
        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': details['name'],
            'description': details.get('description'),
            'formats': formats,
            'thumbnail': urljoin(base_url, details['thumbnailPath']) if 'thumbnailPath' in details else None,
            'uploader': try_get(details, lambda x: x['account']['displayName'], compat_str),
            'uploader_id': try_get(details, lambda x: x['account']['id'], int),
            'uploder_url': try_get(details, lambda x: x['account']['url'], compat_str),
            'duration': int_or_none(details.get('duration')),
            'view_count': int_or_none(details.get('views')),
            'like_count': int_or_none(details.get('likes')),
            'dislike_count': int_or_none(details.get('dislikes')),
            'tags': details.get('tags')
        }
