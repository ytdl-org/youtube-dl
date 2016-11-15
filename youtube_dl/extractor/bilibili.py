# coding: utf-8
from __future__ import unicode_literals

import hashlib
import re

from .common import InfoExtractor
from ..compat import compat_parse_qs
from ..utils import (
    int_or_none,
    float_or_none,
    unified_timestamp,
    urlencode_postdata,
)


class BiliBiliIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|bangumi\.|)bilibili\.(?:tv|com)/(?:video/av|anime/v/)(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.bilibili.tv/video/av1074402/',
        'md5': '9fa226fe2b8a9a4d5a69b4c6a183417e',
        'info_dict': {
            'id': '1074402',
            'ext': 'mp4',
            'title': '【金坷垃】金泡沫',
            'description': 'md5:ce18c2a2d2193f0df2917d270f2e5923',
            'duration': 308.315,
            'timestamp': 1398012660,
            'upload_date': '20140420',
            'thumbnail': 're:^https?://.+\.jpg',
            'uploader': '菊子桑',
            'uploader_id': '156160',
        },
    }

    _APP_KEY = '6f90a59ac58a4123'
    _BILIBILI_KEY = '0bfd84cc3940035173f35e6777508326'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if 'anime/v' not in url:
            cid = compat_parse_qs(self._search_regex(
                [r'EmbedPlayer\([^)]+,\s*"([^"]+)"\)',
                 r'<iframe[^>]+src="https://secure\.bilibili\.com/secure,([^"]+)"'],
                webpage, 'player parameters'))['cid'][0]
        else:
            js = self._download_json(
                'http://bangumi.bilibili.com/web_api/get_source', video_id,
                data=urlencode_postdata({'episode_id': video_id}),
                headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
            cid = js['result']['cid']

        payload = 'appkey=%s&cid=%s&otype=json&quality=2&type=mp4' % (self._APP_KEY, cid)
        sign = hashlib.md5((payload + self._BILIBILI_KEY).encode('utf-8')).hexdigest()

        video_info = self._download_json(
            'http://interface.bilibili.com/playurl?%s&sign=%s' % (payload, sign),
            video_id, note='Downloading video info page')

        entries = []

        for idx, durl in enumerate(video_info['durl']):
            formats = [{
                'url': durl['url'],
                'filesize': int_or_none(durl['size']),
            }]
            for backup_url in durl.get('backup_url', []):
                formats.append({
                    'url': backup_url,
                    # backup URLs have lower priorities
                    'preference': -2 if 'hd.mp4' in backup_url else -3,
                })

            self._sort_formats(formats)

            entries.append({
                'id': '%s_part%s' % (video_id, idx),
                'duration': float_or_none(durl.get('length'), 1000),
                'formats': formats,
            })

        title = self._html_search_regex('<h1[^>]+title="([^"]+)">', webpage, 'title')
        description = self._html_search_meta('description', webpage)
        timestamp = unified_timestamp(self._html_search_regex(
            r'<time[^>]+datetime="([^"]+)"', webpage, 'upload time', fatal=False))
        thumbnail = self._html_search_meta(['og:image', 'thumbnailUrl'], webpage)

        # TODO 'view_count' requires deobfuscating Javascript
        info = {
            'id': video_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'thumbnail': thumbnail,
            'duration': float_or_none(video_info.get('timelength'), scale=1000),
        }

        uploader_mobj = re.search(
            r'<a[^>]+href="https?://space\.bilibili\.com/(?P<id>\d+)"[^>]+title="(?P<name>[^"]+)"',
            webpage)
        if uploader_mobj:
            info.update({
                'uploader': uploader_mobj.group('name'),
                'uploader_id': uploader_mobj.group('id'),
            })

        for entry in entries:
            entry.update(info)

        if len(entries) == 1:
            return entries[0]
        else:
            for idx, entry in enumerate(entries):
                entry['id'] = '%s_part%d' % (video_id, (idx + 1))

            return {
                '_type': 'multi_video',
                'id': video_id,
                'title': title,
                'description': description,
                'entries': entries,
            }
