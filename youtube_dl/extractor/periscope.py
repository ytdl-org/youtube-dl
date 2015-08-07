# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    unescapeHTML,
)


class PeriscopeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?periscope\.tv/w/(?P<id>[^/?#]+)'
    _TEST = {
        'url': 'https://www.periscope.tv/w/aJUQnjY3MjA3ODF8NTYxMDIyMDl2zCg2pECBgwTqRpQuQD352EMPTKQjT4uqlM3cgWFA-g==',
        'md5': '65b57957972e503fcbbaeed8f4fa04ca',
        'info_dict': {
            'id': '56102209',
            'ext': 'mp4',
            'title': 'Bec Boop - 🚠✈️🇬🇧 Fly above #London in Emirates Air Line cable car at night 🇬🇧✈️🚠 #BoopScope 🎀💗',
            'timestamp': 1438978559,
            'upload_date': '20150807',
            'uploader': 'Bec Boop',
            'uploader_id': '1465763',
        },
        'skip': 'Expires in 24 hours',
    }

    def _call_api(self, method, token):
        return self._download_json(
            'https://api.periscope.tv/api/v2/%s?token=%s' % (method, token), token)

    def _real_extract(self, url):
        token = self._match_id(url)

        replay = self._call_api('getAccessPublic', token)
        video_url = replay['replay_url']

        broadcast_data = self._call_api('getBroadcastPublic', token)
        broadcast = broadcast_data['broadcast']
        status = broadcast['status']

        uploader = broadcast.get('user_display_name') or broadcast_data.get('user', {}).get('display_name')
        uploader_id = broadcast.get('user_id') or broadcast_data.get('user', {}).get('id')

        title = '%s - %s' % (uploader, status) if uploader else status
        timestamp = parse_iso8601(broadcast.get('created_at'))

        thumbnails = [{
            'url': broadcast[image],
        } for image in ('image_url', 'image_url_small') if broadcast.get(image)]

        return {
            'id': broadcast.get('id') or token,
            'url': video_url,
            'ext': 'mp4',
            'protocol': 'm3u8_native',
            'title': title,
            'timestamp': timestamp,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'thumbnails': thumbnails,
        }
