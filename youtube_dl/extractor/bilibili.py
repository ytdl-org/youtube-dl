# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import (
    compat_etree_fromstring,
)
from ..utils import (
    int_or_none,
    unescapeHTML,
    ExtractorError,
)


class BiliBiliIE(InfoExtractor):
    _VALID_URL = r'http://www\.bilibili\.(?:tv|com)/video/av(?P<id>\d+)(?:/index_(?P<page_num>\d+).html)?'

    _TESTS = [{
        'url': 'http://www.bilibili.tv/video/av1074402/',
        'md5': '2c301e4dab317596e837c3e7633e7d86',
        'info_dict': {
            'id': '1554319',
            'ext': 'flv',
            'title': '【金坷垃】金泡沫',
            'duration': 308313,
            'upload_date': '20140420',
            'thumbnail': 're:^https?://.+\.jpg',
            'description': 'md5:ce18c2a2d2193f0df2917d270f2e5923',
            'timestamp': 1397983878,
            'uploader': '菊子桑',
        },
    }, {
        'url': 'http://www.bilibili.com/video/av1041170/',
        'info_dict': {
            'id': '1041170',
            'title': '【BD1080P】刀语【诸神&异域】',
            'description': '这是个神奇的故事~每个人不留弹幕不给走哦~切利哦！~',
            'uploader': '枫叶逝去',
            'timestamp': 1396501299,
        },
        'playlist_count': 9,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        page_num = mobj.group('page_num') or '1'

        view_data = self._download_json(
            'http://api.bilibili.com/view?type=json&appkey=8e9fc618fbd41e28&id=%s&page=%s' % (video_id, page_num),
            video_id)
        if 'error' in view_data:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, view_data['error']), expected=True)

        cid = view_data['cid']
        title = unescapeHTML(view_data['title'])

        page = self._download_webpage(
            'http://interface.bilibili.com/v_cdn_play?appkey=8e9fc618fbd41e28&cid=%s' % cid,
            cid,
            'Downloading page %s/%s' % (page_num, view_data['pages'])
        )
        try:
            err_info = json.loads(page)
            raise ExtractorError(
                'BiliBili said: ' + err_info['error_text'], expected=True)
        except ValueError:
            pass

        doc = compat_etree_fromstring(page)

        entries = []

        for durl in doc.findall('./durl'):
            size = durl.find('./filesize|./size')
            formats = [{
                'url': durl.find('./url').text,
                'filesize': int_or_none(size.text) if size else None,
                'ext': 'flv',
            }]
            backup_urls = durl.find('./backup_url')
            if backup_urls is not None:
                for backup_url in backup_urls.findall('./url'):
                    formats.append({'url': backup_url.text})
            formats.reverse()

            entries.append({
                'id': '%s_part%s' % (cid, durl.find('./order').text),
                'title': title,
                'duration': int_or_none(durl.find('./length').text) // 1000,
                'formats': formats,
            })

        info = {
            'id': str(cid),
            'title': title,
            'description': view_data.get('description'),
            'thumbnail': view_data.get('pic'),
            'uploader': view_data.get('author'),
            'timestamp': int_or_none(view_data.get('created')),
            'view_count': view_data.get('play'),
            'duration': int_or_none(doc.find('./timelength').text),
        }

        if len(entries) == 1:
            entries[0].update(info)
            return entries[0]
        else:
            info.update({
                '_type': 'multi_video',
                'id': video_id,
                'entries': entries,
            })
            return info
