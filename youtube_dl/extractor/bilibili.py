# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_parse_qs,
    ExtractorError,
    int_or_none,
    unified_strdate,
)


class BiliBiliIE(InfoExtractor):
    _VALID_URL = r'http://www\.bilibili\.(?:tv|com)/video/av(?P<id>[0-9]+)/'

    _TEST = {
        'url': 'http://www.bilibili.tv/video/av1074402/',
        'md5': '2c301e4dab317596e837c3e7633e7d86',
        'info_dict': {
            'id': '1074402',
            'ext': 'flv',
            'title': '【金坷垃】金泡沫',
            'duration': 308,
            'upload_date': '20140420',
            'thumbnail': 're:^https?://.+\.jpg',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
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

        player_params = compat_parse_qs(self._html_search_regex(
            r'<iframe .*?class="player" src="https://secure\.bilibili\.(?:tv|com)/secure,([^"]+)"',
            webpage, 'player params'))

        if 'cid' in player_params:
            cid = player_params['cid'][0]

            lq_doc = self._download_xml(
                'http://interface.bilibili.cn/v_cdn_play?cid=%s' % cid,
                video_id,
                note='Downloading LQ video info'
            )
            lq_durl = lq_doc.find('.//durl')
            formats = [{
                'format_id': 'lq',
                'quality': 1,
                'url': lq_durl.find('./url').text,
                'filesize': int_or_none(
                    lq_durl.find('./size'), get_attr='text'),
            }]

            hq_doc = self._download_xml(
                'http://interface.bilibili.cn/playurl?cid=%s' % cid,
                video_id,
                note='Downloading HQ video info',
                fatal=False,
            )
            if hq_doc is not False:
                hq_durl = hq_doc.find('.//durl')
                formats.append({
                    'format_id': 'hq',
                    'quality': 2,
                    'ext': 'flv',
                    'url': hq_durl.find('./url').text,
                    'filesize': int_or_none(
                        hq_durl.find('./size'), get_attr='text'),
                })
        else:
            raise ExtractorError('Unsupported player parameters: %r' % (player_params,))

        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'duration': duration,
            'upload_date': upload_date,
            'thumbnail': thumbnail,
        }
