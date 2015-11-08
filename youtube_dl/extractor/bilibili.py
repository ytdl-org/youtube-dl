# coding: utf-8
from __future__ import unicode_literals

import re
import itertools
import json

from .common import InfoExtractor
from ..compat import (
    compat_etree_fromstring,
)
from ..utils import (
    int_or_none,
    unified_strdate,
    ExtractorError,
)


class BiliBiliIE(InfoExtractor):
    _VALID_URL = r'http://www\.bilibili\.(?:tv|com)/video/av(?P<id>[0-9]+)/'

    _TESTS = [{
        'url': 'http://www.bilibili.tv/video/av1074402/',
        'md5': '2c301e4dab317596e837c3e7633e7d86',
        'info_dict': {
            'id': '1074402_part1',
            'ext': 'flv',
            'title': '【金坷垃】金泡沫',
            'duration': 308,
            'upload_date': '20140420',
            'thumbnail': 're:^https?://.+\.jpg',
        },
    }, {
        'url': 'http://www.bilibili.com/video/av1041170/',
        'info_dict': {
            'id': '1041170',
            'title': '【BD1080P】刀语【诸神&异域】',
        },
        'playlist_count': 9,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if '(此视频不存在或被删除)' in webpage:
            raise ExtractorError(
                'The video does not exist or was deleted', expected=True)

        if '>你没有权限浏览！ 由于版权相关问题 我们不对您所在的地区提供服务<' in webpage:
            raise ExtractorError(
                'The video is not available in your region due to copyright reasons',
                expected=True)

        video_code = self._search_regex(
            r'(?s)<div itemprop="video".*?>(.*?)</div>', webpage, 'video code')

        title = self._html_search_meta(
            'media:title', video_code, 'title', fatal=True)
        duration_str = self._html_search_meta(
            'duration', video_code, 'duration')
        if duration_str is None:
            duration = None
        else:
            duration_mobj = re.match(
                r'^T(?:(?P<hours>[0-9]+)H)?(?P<minutes>[0-9]+)M(?P<seconds>[0-9]+)S$',
                duration_str)
            duration = (
                int_or_none(duration_mobj.group('hours'), default=0) * 3600 +
                int(duration_mobj.group('minutes')) * 60 +
                int(duration_mobj.group('seconds')))
        upload_date = unified_strdate(self._html_search_meta(
            'uploadDate', video_code, fatal=False))
        thumbnail = self._html_search_meta(
            'thumbnailUrl', video_code, 'thumbnail', fatal=False)

        cid = self._search_regex(r'cid=(\d+)', webpage, 'cid')

        entries = []

        lq_page = self._download_webpage(
            'http://interface.bilibili.com/v_cdn_play?appkey=1&cid=%s' % cid,
            video_id,
            note='Downloading LQ video info'
        )
        try:
            err_info = json.loads(lq_page)
            raise ExtractorError(
                'BiliBili said: ' + err_info['error_text'], expected=True)
        except ValueError:
            pass

        lq_doc = compat_etree_fromstring(lq_page)
        lq_durls = lq_doc.findall('./durl')

        hq_doc = self._download_xml(
            'http://interface.bilibili.com/playurl?appkey=1&cid=%s' % cid,
            video_id,
            note='Downloading HQ video info',
            fatal=False,
        )
        if hq_doc is not False:
            hq_durls = hq_doc.findall('./durl')
            assert len(lq_durls) == len(hq_durls)
        else:
            hq_durls = itertools.repeat(None)

        i = 1
        for lq_durl, hq_durl in zip(lq_durls, hq_durls):
            formats = [{
                'format_id': 'lq',
                'quality': 1,
                'url': lq_durl.find('./url').text,
                'filesize': int_or_none(
                    lq_durl.find('./size'), get_attr='text'),
            }]
            if hq_durl is not None:
                formats.append({
                    'format_id': 'hq',
                    'quality': 2,
                    'ext': 'flv',
                    'url': hq_durl.find('./url').text,
                    'filesize': int_or_none(
                        hq_durl.find('./size'), get_attr='text'),
                })
            self._sort_formats(formats)

            entries.append({
                'id': '%s_part%d' % (video_id, i),
                'title': title,
                'formats': formats,
                'duration': duration,
                'upload_date': upload_date,
                'thumbnail': thumbnail,
            })

            i += 1

        return {
            '_type': 'multi_video',
            'entries': entries,
            'id': video_id,
            'title': title
        }
