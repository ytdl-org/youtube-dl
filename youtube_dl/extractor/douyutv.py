# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class DouyuTVIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?douyutv\.com/(?P<id>[A-Za-z0-9]+)'
    _TEST = {
        'url': 'http://www.douyutv.com/iseven',
        'info_dict': {
            'id': 'iseven',
            'ext': 'flv',
            'title': 're:^清晨醒脑！T-ara根本停不下来！ [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'md5:9e525642c25a0a24302869937cf69d17',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': '7师傅',
            'uploader_id': '431925',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        config = self._download_json(
            'http://www.douyutv.com/api/client/room/%s' % video_id, video_id)

        data = config['data']

        error_code = config.get('error', 0)
        show_status = data.get('show_status')
        if error_code is not 0:
            raise ExtractorError(
                'Server reported error %i' % error_code, expected=True)

        # 1 = live, 2 = offline
        if show_status == '2':
            raise ExtractorError(
                'Live stream is offline', expected=True)

        base_url = data['rtmp_url']
        live_path = data['rtmp_live']

        title = self._live_title(data['room_name'])
        description = data.get('show_details')
        thumbnail = data.get('room_src')

        uploader = data.get('nickname')
        uploader_id = data.get('owner_uid')

        multi_formats = data.get('rtmp_multi_bitrate')
        if not isinstance(multi_formats, dict):
            multi_formats = {}
        multi_formats['live'] = live_path

        formats = [{
            'url': '%s/%s' % (base_url, format_path),
            'format_id': format_id,
            'preference': 1 if format_id == 'live' else 0,
        } for format_id, format_path in multi_formats.items()]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'formats': formats,
            'is_live': True,
        }
