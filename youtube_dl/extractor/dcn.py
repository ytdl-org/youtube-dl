# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    int_or_none,
    parse_iso8601,
)


class DCNGeneralIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dcndigital\.ae/(?:#/)?show/(?P<show_id>\d+)/[^/]+(?:/(?P<video_id>\d+)/(?P<season_id>\d+))?'

    def _real_extract(self, url):
        show_id, video_id, season_id = re.match(self._VALID_URL, url).groups()
        url = ''
        ie_key = ''
        if video_id and int(video_id) > 0:
            url = 'http://www.dcndigital.ae/#/media/%s' % video_id
            ie_key = 'DCNVideo'
        else:
            ie_key = 'DCNShow'
            if season_id and int(season_id) > 0:
                url = 'http://www.dcndigital.ae/#/program/season/%s' % season_id
            else:
                url = 'http://www.dcndigital.ae/#/program/%s' % show_id
        return {
            'url': url,
            '_type': 'url',
            'ie_key': ie_key
        }


class DCNVideoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dcndigital\.ae/(?:#/)?(?:video/[^/]+|media)/(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.dcndigital.ae/#/video/%D8%B1%D8%AD%D9%84%D8%A9-%D8%A7%D9%84%D8%B9%D9%85%D8%B1-%D8%A7%D9%84%D8%AD%D9%84%D9%82%D8%A9-1/17375',
        'info_dict':
        {
            'id': '17375',
            'ext': 'mp4',
            'title': 'رحلة العمر : الحلقة 1',
            'description': 'md5:0156e935d870acb8ef0a66d24070c6d6',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 2041,
            'timestamp': 1227504126,
            'upload_date': '20081124',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        request = compat_urllib_request.Request(
            'http://admin.mangomolo.com/analytics/index.php/plus/video?id=%s' % video_id,
            headers={'Origin': 'http://www.dcndigital.ae'})

        video = self._download_json(request, video_id)
        title = video.get('title_en') or video['title_ar']

        webpage = self._download_webpage(
            'http://admin.mangomolo.com/analytics/index.php/customers/embed/video?'
            + compat_urllib_parse.urlencode({
                'id': video['id'],
                'user_id': video['user_id'],
                'signature': video['signature'],
                'countries': 'Q0M=',
                'filter': 'DENY',
            }), video_id)

        m3u8_url = self._html_search_regex(r'file:\s*"([^"]+)', webpage, 'm3u8 url')
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls')

        rtsp_url = self._search_regex(
            r'<a[^>]+href="(rtsp://[^"]+)"', webpage, 'rtsp url', fatal=False)
        if rtsp_url:
            formats.append({
                'url': rtsp_url,
                'format_id': 'rtsp',
            })

        self._sort_formats(formats)

        img = video.get('img')
        thumbnail = 'http://admin.mangomolo.com/analytics/%s' % img if img else None
        duration = int_or_none(video.get('duration'))
        description = video.get('description_en') or video.get('description_ar')
        timestamp = parse_iso8601(video.get('create_time') or video.get('update_time'), ' ')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'timestamp': timestamp,
            'formats': formats,
        }


class DCNShowIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dcndigital\.ae/(?:#/)?program/(?:(?P<show_id>\d+)|season/(?P<season_id>\d+))'
    _TEST = {
        'url': 'http://dcndigital.ae/#/program/205024/%D9%85%D8%AD%D8%A7%D8%B6%D8%B1%D8%A7%D8%AA-%D8%A7%D9%84%D8%B4%D9%8A%D8%AE-%D8%A7%D9%84%D8%B4%D8%B9%D8%B1%D8%A7%D9%88%D9%8A',
        'info_dict':
        {
            'id': '205024',
            'title': 'محاضرات الشيخ الشعراوي',
            'description': '',
        },
        'playlist_mincount': 27,
    }

    def _real_extract(self, url):
        show_id, season_id = re.match(self._VALID_URL, url).groups()
        data = {}
        if season_id:
            request = compat_urllib_request.Request(
                'http://admin.mangomolo.com/analytics/index.php/plus/season_info?id=%s' % season_id,
                headers={'Origin': 'http://www.dcndigital.ae'})
            season = self._download_json(request, season_id)
            show_id = season['id']
            data['season'] = season_id
        data['show_id'] = show_id
        request = compat_urllib_request.Request(
            'http://admin.mangomolo.com/analytics/index.php/plus/show',
            compat_urllib_parse.urlencode(data),
            {
                'Origin': 'http://www.dcndigital.ae',
                'Content-Type': 'application/x-www-form-urlencoded'
            })
        show = self._download_json(request, show_id)
        title = show['cat'].get('title_en') or show['cat']['title_ar']
        description = show['cat'].get('description_en') or show['cat'].get('description_ar')
        entries = []
        for video in show['videos']:
            entries.append({
                'url': 'http://www.dcndigital.ae/#/media/%s' % video['id'],
                '_type': 'url',
                'ie_key': 'DCNVideo',
            })
        return {
            'id': show_id,
            'title': title,
            'description': description,
            'entries': entries,
            '_type': 'playlist',
        }
