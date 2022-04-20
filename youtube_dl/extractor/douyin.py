# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    int_or_none,
    try_get,
    orderedSet
)


class DouyinVideoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?douyin\.com/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.douyin.com/video/6989098563519270181',
        'md5': '99c5667992b8a8d46c145907f677c92b',
        'info_dict': {
            'id': '6989098563519270181',
            'url': 'https://aweme.snssdk.com/aweme/v1/playwm/?video_id=v0300fg10000c3v47dbc77u9fvb20tbg&ratio=720p&line=0',
            'title': '杨集#我的家乡 ',
            'uploader': '🌹永恒的爱🌹',
            'uploader_id': '104081949894',
            'timestamp': 1627276320000.0,
            'ext': 'mp4'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        iteminfo = self._download_json('https://www.douyin.com/web/api/v2/aweme/iteminfo',
                                       video_id, query={'item_ids': video_id}) or {}
        status_code = iteminfo.get('status_code', 'status_code missing')
        if status_code:
            raise ExtractorError('%s (%s)' % (iteminfo.get('status_msg', 'status_msg missing'), status_code), video_id=video_id)

        item_list = iteminfo.get('item_list')
        if not item_list:
            raise ExtractorError('The video you want to download does not exist any more',
                                 video_id=video_id, expected=True)
        item = item_list[0]

        return {
            'id': video_id,
            'title': item['desc'],
            'url': item['video']['play_addr']['url_list'][0],
            'uploader': try_get(item, lambda x: x['author']['nickname'], compat_str),
            'uploader_id': try_get(item, lambda x: x['author']['uid'], compat_str),
            'duration': int_or_none(item.get('duration') or try_get(item, lambda x: x['video']['duration'], int), scale=1000),
            'timestamp': int_or_none(item.get('create_time'), invscale=1000),
            'width': try_get(item, lambda x: x['video']['width'], int),
            'height': try_get(item, lambda x: x['video']['height'], int),
            'vbr': try_get(item, lambda x: x['video']['bit_rate'], int),
            'ext': 'mp4'
        }


class DouyinUserIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?douyin\.com/user/(?P<id>[a-zA-Z0-9_\-]+)'
    _TEST = {
        'url': 'https://www.douyin.com/user/MS4wLjABAAAAP5Q7Z-SwleIzAACYIu-LrwGbEZzN2dc5PT3hGNSTkSM',
        'info_dict': {
            'id': 'MS4wLjABAAAAP5Q7Z-SwleIzAACYIu-LrwGbEZzN2dc5PT3hGNSTkSM'
        },
        'playlist_mincount': 31
    }

    def _real_extract(self, url):
        sec_uid = self._match_id(url)

        has_more = True
        max_cursor = ''

        entries = []
        while has_more:
            post = self._download_json('https://www.douyin.com/web/api/v2/aweme/post',
                                       sec_uid, query={'sec_uid': sec_uid, 'max_cursor': max_cursor, 'count': 50}) or {}
            status_code = post.get('status_code', 'status_code missing')
            if status_code:
                raise ExtractorError('%s (%s)' % (post.get('status_msg', 'status_msg missing'), status_code), video_id=sec_uid)

            aweme_list = post.get('aweme_list')
            if aweme_list is None:
                raise ExtractorError('JSON response does not contain aweme_list', video_id=sec_uid)

            entries.extend([self.url_result('https://www.douyin.com/video/%s' % aweme_id,
                                            ie=DouyinVideoIE.ie_key(), video_id=aweme_id)
                            for aweme_id in filter(None,
                                                   (aweme.get('aweme_id') for aweme in aweme_list
                                                    if isinstance(aweme, dict)))])

            has_more = post.get('has_more')
            max_cursor = post.get('max_cursor')

        return self.playlist_result(orderedSet(entries), sec_uid)
