# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    try_get,
    orderedSet
)


class DouyinVideoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?douyin\.com/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.douyin.com/video/6989098563519270181',
        'md5': 'b4c99f3be1be343948a9eaaea8303d27',
        'info_dict': {
            'id': '6989098563519270181',
            'url': r're:^https://v3-dy-o.zjcdn.com/[0-9a-f]{32}/[0-9a-f]{8}/video/tos/cn/tos-cn-ve-15/[0-9a-f]{32}/?.*',
            'title': '杨集#我的家乡 ',
            'uploader': '永恒的爱',
            'uploader_id': '104081949894',
            'timestamp': 1627276320000.0,
            'ext': 'mp4'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        iteminfo = self._download_json('https://www.douyin.com/web/api/v2/aweme/iteminfo',
                                       video_id, query={'item_ids': video_id})
        if iteminfo['status_code']:
            raise ExtractorError(iteminfo['status_msg'], video_id=video_id)

        item_list = iteminfo.get('item_list')
        if not item_list:
            raise ExtractorError('The video you want to download does not exist any more',
                                 video_id=video_id, expected=True)
        item = item_list[0]

        info_dict = {}
        info_dict['id'] = video_id
        info_dict['title'] = item['desc']
        info_dict['url'] = item['video']['play_addr']['url_list'][0]
        info_dict['uploader'] = try_get(item, lambda x: x['author']['nickname'])
        info_dict['uploader_id'] = try_get(item, lambda x: x['author']['uid'])
        info_dict['duration'] = float_or_none(item.get('duration') or try_get(item, lambda x: x['video']['duration'], int), scale=1000)
        info_dict['timestamp'] = float_or_none(item.get('create_time'), invscale=1000)
        info_dict['width'] = try_get(item, lambda x: x['video']['width'])
        info_dict['height'] = try_get(item, lambda x: x['video']['height'])
        info_dict['vbr'] = try_get(item, lambda x: x['video']['bit_rate'])
        info_dict['ext'] = 'mp4'

        return info_dict


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
                                       sec_uid, query={'sec_uid': sec_uid, 'max_cursor': max_cursor, 'count': 50})
            if post['status_code']:
                raise ExtractorError(post['status_msg'], video_id=sec_uid)

            aweme_list = post.get('aweme_list')
            if aweme_list is None:
                raise ExtractorError('JSON response does not contain aweme_list', video_id=sec_uid)

            entries.extend([self.url_result('https://www.douyin.com/video/%s' % aweme['aweme_id'],
                                            ie=DouyinVideoIE.ie_key(), video_id=aweme['aweme_id'])
                            for aweme in aweme_list])

            has_more = post['has_more']
            max_cursor = post['max_cursor']

        return self.playlist_result(orderedSet(entries), sec_uid)

