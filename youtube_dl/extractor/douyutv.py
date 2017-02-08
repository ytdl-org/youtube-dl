# coding: utf-8
from __future__ import unicode_literals

import hashlib
import time
import uuid

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urllib_parse_urlencode,
)
from ..utils import (
    ExtractorError,
    unescapeHTML,
)


class DouyuTVIE(InfoExtractor):
    IE_DESC = '斗鱼'
    _VALID_URL = r'https?://(?:www\.)?douyu(?:tv)?\.com/(?:[^/]+/)*(?P<id>[A-Za-z0-9]+)'
    _TESTS = [{
        'url': 'http://www.douyutv.com/iseven',
        'info_dict': {
            'id': '17732',
            'display_id': 'iseven',
            'ext': 'flv',
            'title': 're:^清晨醒脑！T-ara根本停不下来！ [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': r're:.*m7show@163\.com.*',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': '7师傅',
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
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'douyu小漠',
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
            'description': r're:.*m7show@163\.com.*',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': '7师傅',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.douyu.com/xiaocang',
        'only_matching': True,
    }, {
        # \"room_id\"
        'url': 'http://www.douyu.com/t/lpl',
        'only_matching': True,
    }]

    # Decompile core.swf in webpage by ffdec "Search SWFs in memory". core.swf
    # is encrypted originally, but ffdec can dump memory to get the decrypted one.
    _API_KEY = 'A12Svb&%1UUmf@hC'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        if video_id.isdigit():
            room_id = video_id
        else:
            page = self._download_webpage(url, video_id)
            room_id = self._html_search_regex(
                r'"room_id\\?"\s*:\s*(\d+),', page, 'room id')

        room = self._download_json(
            'http://m.douyu.com/html5/live?roomId=%s' % room_id, video_id,
            note='Downloading room info')['data']

        # 1 = live, 2 = offline
        if room.get('show_status') == '2':
            raise ExtractorError('Live stream is offline', expected=True)

        tt = compat_str(int(time.time() / 60))
        did = uuid.uuid4().hex.upper()

        sign_content = ''.join((room_id, did, self._API_KEY, tt))
        sign = hashlib.md5((sign_content).encode('utf-8')).hexdigest()

        flv_data = compat_urllib_parse_urlencode({
            'cdn': 'ws',
            'rate': '0',
            'tt': tt,
            'did': did,
            'sign': sign,
        })

        video_info = self._download_json(
            'http://www.douyu.com/lapi/live/getPlay/%s' % room_id, video_id,
            data=flv_data, note='Downloading video info',
            headers={'Content-Type': 'application/x-www-form-urlencoded'})

        error_code = video_info.get('error', 0)
        if error_code is not 0:
            raise ExtractorError(
                '%s reported error %i' % (self.IE_NAME, error_code),
                expected=True)

        base_url = video_info['data']['rtmp_url']
        live_path = video_info['data']['rtmp_live']

        video_url = '%s/%s' % (base_url, live_path)

        title = self._live_title(unescapeHTML(room['room_name']))
        description = room.get('notice')
        thumbnail = room.get('room_src')
        uploader = room.get('nickname')

        return {
            'id': room_id,
            'display_id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'is_live': True,
        }
