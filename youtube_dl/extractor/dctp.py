# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str


class DctpTvIE(InfoExtractor):
    _VALID_URL = r'https?://www.dctp.tv/(#/)?filme/(?P<id>.+?)/$'
    _TEST = {
        'url': 'http://www.dctp.tv/filme/videoinstallation-fuer-eine-kaufhausfassade/',
        'info_dict': {
            'id': '1324',
            'display_id': 'videoinstallation-fuer-eine-kaufhausfassade',
            'ext': 'flv',
            'title': 'Videoinstallation für eine Kaufhausfassade'
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        base_url = 'http://dctp-ivms2-restapi.s3.amazonaws.com/'
        version_json = self._download_json(
            base_url + 'version.json',
            video_id, note='Determining file version')
        version = version_json['version_name']
        info_json = self._download_json(
            '{0}{1}/restapi/slugs/{2}.json'.format(base_url, version, video_id),
            video_id, note='Fetching object ID')
        object_id = compat_str(info_json['object_id'])
        meta_json = self._download_json(
            '{0}{1}/restapi/media/{2}.json'.format(base_url, version, object_id),
            video_id, note='Downloading metadata')
        uuid = meta_json['uuid']
        title = meta_json['title']
        wide = meta_json['is_wide']
        if wide:
            ratio = '16x9'
        else:
            ratio = '4x3'
        play_path = 'mp4:{0}_dctp_0500_{1}.m4v'.format(uuid, ratio)

        servers_json = self._download_json(
            'http://www.dctp.tv/streaming_servers/',
            video_id, note='Downloading server list')
        url = servers_json[0]['endpoint']

        return {
            'id': object_id,
            'title': title,
            'format': 'rtmp',
            'url': url,
            'play_path': play_path,
            'rtmp_real_time': True,
            'ext': 'flv',
            'display_id': video_id
        }
