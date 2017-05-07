# coding: utf-8
from __future__ import unicode_literals

import time
import hashlib
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unescapeHTML,
    compat_HTMLParser
)


class RoomIDParser(compat_HTMLParser):

    def __init__(self, room_index=None):
        compat_HTMLParser.__init__(self)
        self._room_index = room_index
        self._room_id = None

    def handle_starttag(self, tag, attrs):
        if tag != 'div' and tag != 'li':
            return

        attrs_dict = dict(attrs)
        # process switch button situation firstly
        if(tag == 'li'
           and attrs_dict.get('class', '') == 'switchRoom-btn'
           and attrs_dict.get('data-index', '-1') == self._room_index):
            self._room_id = attrs_dict.get('data-onlineid')

        if self._room_id is not None:
            return

        if tag == 'div' and attrs_dict.get('data-component-id', '') == 'room':
            self._room_id = attrs_dict.get('data-onlineid')

    @property
    def room_id(self):
        return self._room_id


class DouyuTVIE(InfoExtractor):
    IE_DESC = '斗鱼'
    _VALID_URL = r'https?://(?:www\.)?douyu(?:tv)?\.com/(?P<id>(?:[^/]+/)*[A-Za-z0-9]+(?:\?roomIndex=\d+)?)'
    _TESTS = [{
        'url': 'http://www.douyutv.com/iseven',
        'info_dict': {
            'id': '17732',
            'display_id': 'iseven',
            'ext': 'flv',
            'title': 're:^清晨醒脑！根本停不下来！ [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
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
            'title': 're:^清晨醒脑！根本停不下来！ [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
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
    }, {
        'url': 'http://www.douyu.com/t/douyukpl?roomIndex=1',
        'only_matching': True
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        if video_id.isdigit():
            room_id = video_id
        else:
            page = self._download_webpage(url, video_id)
            if not video_id.startswith('t/'):
                room_id = self._html_search_regex(
                        r'"room_id\\?"\s*:\s*(\d+),', page, 'room id')
            else:
                match_obj = re.match(r'.+roomIndex=(\d+)', video_id)
                # default room index is 0
                room_index = match_obj.group(1) if match_obj is not None else '0'
                room_id_parser = RoomIDParser(room_index)
                room_id_parser.feed(page)
                room_id = room_id_parser.room_id
                if room_id is None:
                    raise ExtractorError('Extracting room id failed.')

        # Grab metadata from mobile API
        room = self._download_json(
            'http://m.douyu.com/html5/live?roomId=%s' % room_id, video_id,
            note='Downloading room info')['data']

        # 1 = live, 2 = offline
        if room.get('show_status') == '2':
            raise ExtractorError('Live stream is offline', expected=True)

        # Grab the URL from PC client API
        # The m3u8 url from mobile API requires re-authentication every 5 minutes
        tt = int(time.time())
        signContent = 'lapi/live/thirdPart/getPlay/%s?aid=pcclient&rate=0&time=%d9TUk5fjjUjg9qIMH3sdnh' % (room_id, tt)
        sign = hashlib.md5(signContent.encode('ascii')).hexdigest()
        video_url = self._download_json(
            'http://coapi.douyucdn.cn/lapi/live/thirdPart/getPlay/' + room_id,
            video_id, note='Downloading video URL info',
            query={'rate': 0}, headers={
                'auth': sign,
                'time': str(tt),
                'aid': 'pcclient'
            })['data']['live_url']

        title = self._live_title(unescapeHTML(room['room_name']))
        description = room.get('show_details')
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
