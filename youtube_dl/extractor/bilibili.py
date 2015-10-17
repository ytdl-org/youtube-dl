# coding: utf-8
from __future__ import unicode_literals

import json
import xml.etree.ElementTree as ET

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    ExtractorError,
)


class BiliBiliIE(InfoExtractor):
    _VALID_URL = r'http://www\.bilibili\.(?:tv|com)/video/av(?P<id>[0-9]+)/'

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
        },
        'playlist_count': 12,
    }]

    def _extract_video_info(self, cid, view_data, page_num=1, num_pages=1):
        title = view_data['title']

        page = self._download_webpage(
            'http://interface.bilibili.com/v_cdn_play?appkey=8e9fc618fbd41e28&cid=%s' % cid,
            cid,
            'Downloading page %d/%d' % (page_num, num_pages)
        )
        try:
            err_info = json.loads(page)
            raise ExtractorError(
                'BiliBili said: ' + err_info['error_text'], expected=True)
        except ValueError:
            pass

        doc = ET.fromstring(page)
        durls = doc.findall('./durl')

        entries = []

        for durl in durls:
            formats = []
            backup_url = durl.find('./backup_url')
            if backup_url is not None:
                formats.append({'url': backup_url.find('./url').text})
            size = durl.find('./filesize|./size')
            formats.append({
                'url': durl.find('./url').text,
                'filesize': int_or_none(size.text) if size else None,
                'ext': 'flv',
            })
            entries.append({
                'id': '%s_part%s' % (cid, durl.find('./order').text),
                'title': title,
                'duration': int_or_none(durl.find('./length').text) // 1000,
                'formats': formats,
            })

        info = {
            'id': cid,
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
                'entries': entries,
            })
            return info

    def _real_extract(self, url):
        video_id = self._match_id(url)
        view_data = self._download_json('http://api.bilibili.com/view?type=json&appkey=8e9fc618fbd41e28&id=%s' % video_id, video_id)

        num_pages = int_or_none(view_data['pages'])
        if num_pages > 1:
            play_list_title = view_data['title']
            page_list = self._download_json('http://www.bilibili.com/widget/getPageList?aid=%s' % video_id, video_id, 'Downloading page list metadata')
            entries = []
            for page in page_list:
                view_data['title'] = page['pagename']
                entries.append(self._extract_video_info(str(page['cid']), view_data, page['page'], num_pages))
            return self.playlist_result(entries, video_id, play_list_title, view_data.get('description'))
        else:
            return self._extract_video_info(str(view_data['cid']), view_data)
