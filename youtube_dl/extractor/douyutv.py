# coding: utf-8
from __future__ import unicode_literals

import hashlib
import time
from .common import InfoExtractor
from ..utils import (ExtractorError, unescapeHTML)
from ..compat import (compat_str, compat_basestring)


class DouyuTVIE(InfoExtractor):
    IE_DESC = '斗鱼'
    _VALID_URL = r'https?://(?:www\.)?douyu(?:tv)?\.com/(?P<id>[A-Za-z0-9]+)'
    _TESTS = [{
        'url': 'http://www.douyutv.com/iseven',
        'info_dict': {
            'id': '17732',
            'display_id': 'iseven',
            'ext': 'flv',
            'title': 're:^清晨醒脑！T-ara根本停不下来！ [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 're:.*m7show@163\.com.*',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': '7师傅',
            'uploader_id': '431925',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.douyutv.com/85982',
        'info_dict': {
            'id': '85982',
            'display_id': '85982',
            'ext': 'flv',
            'title': 're:^小漠从零单排记！——CSOL2躲猫猫 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'md5:746a2f7a253966a06755a912f0acc0d2',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'douyu小漠',
            'uploader_id': '3769985',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Room not found',
    }, {
        'url': 'http://www.douyutv.com/17732',
        'info_dict': {
            'id': '17732',
            'display_id': '17732',
            'ext': 'flv',
            'title': 're:^清晨醒脑！T-ara根本停不下来！ [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 're:.*m7show@163\.com.*',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': '7师傅',
            'uploader_id': '431925',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.douyu.com/xiaocang',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        if video_id.isdigit():
            room_id = video_id
        else:
            page = self._download_webpage(url, video_id)
            room_id = self._html_search_regex(
                r'"room_id"\s*:\s*(\d+),', page, 'room id')

        config = None
        # Douyu API sometimes returns error "Unable to load the requested class: eticket_redis_cache"
        # Retry with different parameters - same parameters cause same errors
        for i in range(5):
            prefix = 'room/%s?aid=android&client_sys=android&time=%d' % (
                room_id, int(time.time()))
            auth = hashlib.md5((prefix + '1231').encode('ascii')).hexdigest()

            config_page = self._download_webpage(
                'http://www.douyutv.com/api/v1/%s&auth=%s' % (prefix, auth),
                video_id)
            try:
                config = self._parse_json(config_page, video_id, fatal=False)
            except ExtractorError:
                # Wait some time before retrying to get a different time() value
                self._sleep(1, video_id, msg_template='%(video_id)s: Error occurs. '
                                                      'Waiting for %(timeout)s seconds before retrying')
                continue
            else:
                break
        if config is None:
            raise ExtractorError('Unable to fetch API result')

        data = config['data']

        error_code = config.get('error', 0)
        if error_code is not 0:
            error_desc = 'Server reported error %i' % error_code
            if isinstance(data, (compat_str, compat_basestring)):
                error_desc += ': ' + data
            raise ExtractorError(error_desc, expected=True)

        show_status = data.get('show_status')
        # 1 = live, 2 = offline
        if show_status == '2':
            raise ExtractorError(
                'Live stream is offline', expected=True)

        base_url = data['rtmp_url']
        live_path = data['rtmp_live']

        title = self._live_title(unescapeHTML(data['room_name']))
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
            'id': room_id,
            'display_id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'formats': formats,
            'is_live': True,
        }
