# coding: utf-8
from __future__ import unicode_literals

import hmac
from hashlib import sha1
from base64 import b64encode
from time import time

from .naver import NaverIE
from ..utils import (
    ExtractorError,
    int_or_none,
)
from ..compat import compat_urllib_parse


class VLiveIE(NaverIE):
    IE_NAME = 'vlive'
    # www.vlive.tv/video/ links redirect to m.vlive.tv/video/ for mobile devices
    _VALID_URL = r'https?://(?:(www|m)\.)?vlive\.tv/video/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://m.vlive.tv/video/1326',
        'md5': 'cc7314812855ce56de70a06a27314983',
        'info_dict': {
            'id': '1326',
            'ext': 'mp4',
            'title': '[V] Girl\'s Day\'s Broadcast',
            'creator': 'Girl\'s Day',
        },
    }]
    _SECRET = 'rFkwZet6pqk1vQt6SxxUkAHX7YL3lmqzUMrU4IDusTo4jEBdtOhNfT4BYYAdArwH'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        status = self._download_json(
            'http://www.vlive.tv/video/status?videoSeq=%s' % video_id,
            video_id, note='Download status metadata')

        vid = status.get('vodId')
        if vid:
            key = status.get('vodInKey')
            if not key:
                key = self._download_webpage('http://www.vlive.tv/video/inkey?vodId=%s' % vid, video_id)
            if key:
                video_info = self._extract_video_info(vid, key)
        elif status['status'] not in ('CANCELED', 'COMING_SOON', 'NOT_FOUND'):
            webpage = self._download_webpage(
                'http://m.vlive.tv/video/%s' % video_id,
                video_id, note='Download video page')
            title = self._og_search_title(webpage)
            thumbnail = self._og_search_thumbnail(webpage)
            creator = self._html_search_regex(
                r'<span[^>]+class="name">([^<>]+)</span>', webpage, 'creator')
            url = 'http://global.apis.naver.com/globalV/globalV/vod/%s/playinfo?' % video_id
            msgpad = '%.0f' % (time() * 1000)
            md = b64encode(
                hmac.new(self._SECRET.encode('ascii'),
                         (url[:255] + msgpad).encode('ascii'), sha1).digest()
            )
            url += '&' + compat_urllib_parse.urlencode({'msgpad': msgpad, 'md': md})
            playinfo = self._download_json(url, video_id, 'Downloading video json')
            if playinfo.get('message', '') != 'success':
                raise ExtractorError(playinfo.get('message', 'JSON request unsuccessful'))
            result = playinfo.get('result')
            if not result:
                raise ExtractorError('No videos found.')
            video_info = self._parse_video_info(result, video_id)
            video_info.update({
                'title': title,
                'thumbnail': thumbnail,
                'creator': creator,
            })
        if video_info:
            video_info.update({
                'id': video_id,
                'view_count': int_or_none(status.get('playCount')),
                'likes': int_or_none(status.get('likeCount')),
            })
            return video_info
        raise ExtractorError(status['status'])
