# coding: utf-8
from __future__ import unicode_literals

import re
import base64

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlencode,
    compat_str,
)
from ..utils import (
    int_or_none,
    parse_iso8601,
    sanitized_Request,
    smuggle_url,
    unsmuggle_url,
    urlencode_postdata,
)


class DCNIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dcndigital\.ae/(?:#/)?show/(?P<show_id>\d+)/[^/]+(?:/(?P<video_id>\d+)/(?P<season_id>\d+))?'

    def _real_extract(self, url):
        show_id, video_id, season_id = re.match(self._VALID_URL, url).groups()
        if video_id and int(video_id) > 0:
            return self.url_result(
                'http://www.dcndigital.ae/media/%s' % video_id, 'DCNVideo')
        elif season_id and int(season_id) > 0:
            return self.url_result(smuggle_url(
                'http://www.dcndigital.ae/program/season/%s' % season_id,
                {'show_id': show_id}), 'DCNSeason')
        else:
            return self.url_result(
                'http://www.dcndigital.ae/program/%s' % show_id, 'DCNSeason')


class DCNBaseIE(InfoExtractor):
    def _extract_video_info(self, video_data, video_id, is_live):
        title = video_data.get('title_en') or video_data['title_ar']
        img = video_data.get('img')
        thumbnail = 'http://admin.mangomolo.com/analytics/%s' % img if img else None
        duration = int_or_none(video_data.get('duration'))
        description = video_data.get('description_en') or video_data.get('description_ar')
        timestamp = parse_iso8601(video_data.get('create_time'), ' ')

        return {
            'id': video_id,
            'title': self._live_title(title) if is_live else title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'timestamp': timestamp,
            'is_live': is_live,
        }

    def _extract_video_formats(self, webpage, video_id, entry_protocol):
        formats = []
        m3u8_url = self._html_search_regex(
            r'file\s*:\s*"([^"]+)', webpage, 'm3u8 url', fatal=False)
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', entry_protocol, m3u8_id='hls', fatal=None))

        rtsp_url = self._search_regex(
            r'<a[^>]+href="(rtsp://[^"]+)"', webpage, 'rtsp url', fatal=False)
        if rtsp_url:
            formats.append({
                'url': rtsp_url,
                'format_id': 'rtsp',
            })

        self._sort_formats(formats)
        return formats


class DCNVideoIE(DCNBaseIE):
    IE_NAME = 'dcn:video'
    _VALID_URL = r'https?://(?:www\.)?dcndigital\.ae/(?:#/)?(?:video/[^/]+|media|catchup/[^/]+/[^/]+)/(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.dcndigital.ae/#/video/%D8%B1%D8%AD%D9%84%D8%A9-%D8%A7%D9%84%D8%B9%D9%85%D8%B1-%D8%A7%D9%84%D8%AD%D9%84%D9%82%D8%A9-1/17375',
        'info_dict':
        {
            'id': '17375',
            'ext': 'mp4',
            'title': 'رحلة العمر : الحلقة 1',
            'description': 'md5:0156e935d870acb8ef0a66d24070c6d6',
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

        request = sanitized_Request(
            'http://admin.mangomolo.com/analytics/index.php/plus/video?id=%s' % video_id,
            headers={'Origin': 'http://www.dcndigital.ae'})
        video_data = self._download_json(request, video_id)
        info = self._extract_video_info(video_data, video_id, False)

        webpage = self._download_webpage(
            'http://admin.mangomolo.com/analytics/index.php/customers/embed/video?' +
            compat_urllib_parse_urlencode({
                'id': video_data['id'],
                'user_id': video_data['user_id'],
                'signature': video_data['signature'],
                'countries': 'Q0M=',
                'filter': 'DENY',
            }), video_id)
        info['formats'] = self._extract_video_formats(webpage, video_id, 'm3u8_native')
        return info


class DCNLiveIE(DCNBaseIE):
    IE_NAME = 'dcn:live'
    _VALID_URL = r'https?://(?:www\.)?dcndigital\.ae/(?:#/)?live/(?P<id>\d+)'

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        request = sanitized_Request(
            'http://admin.mangomolo.com/analytics/index.php/plus/getchanneldetails?channel_id=%s' % channel_id,
            headers={'Origin': 'http://www.dcndigital.ae'})

        channel_data = self._download_json(request, channel_id)
        info = self._extract_video_info(channel_data, channel_id, True)

        webpage = self._download_webpage(
            'http://admin.mangomolo.com/analytics/index.php/customers/embed/index?' +
            compat_urllib_parse_urlencode({
                'id': base64.b64encode(channel_data['user_id'].encode()).decode(),
                'channelid': base64.b64encode(channel_data['id'].encode()).decode(),
                'signature': channel_data['signature'],
                'countries': 'Q0M=',
                'filter': 'DENY',
            }), channel_id)
        info['formats'] = self._extract_video_formats(webpage, channel_id, 'm3u8')
        return info


class DCNSeasonIE(InfoExtractor):
    IE_NAME = 'dcn:season'
    _VALID_URL = r'https?://(?:www\.)?dcndigital\.ae/(?:#/)?program/(?:(?P<show_id>\d+)|season/(?P<season_id>\d+))'
    _TEST = {
        'url': 'http://dcndigital.ae/#/program/205024/%D9%85%D8%AD%D8%A7%D8%B6%D8%B1%D8%A7%D8%AA-%D8%A7%D9%84%D8%B4%D9%8A%D8%AE-%D8%A7%D9%84%D8%B4%D8%B9%D8%B1%D8%A7%D9%88%D9%8A',
        'info_dict':
        {
            'id': '7910',
            'title': 'محاضرات الشيخ الشعراوي',
        },
        'playlist_mincount': 27,
    }

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        show_id, season_id = re.match(self._VALID_URL, url).groups()

        data = {}
        if season_id:
            data['season'] = season_id
            show_id = smuggled_data.get('show_id')
            if show_id is None:
                request = sanitized_Request(
                    'http://admin.mangomolo.com/analytics/index.php/plus/season_info?id=%s' % season_id,
                    headers={'Origin': 'http://www.dcndigital.ae'})
                season = self._download_json(request, season_id)
                show_id = season['id']
        data['show_id'] = show_id
        request = sanitized_Request(
            'http://admin.mangomolo.com/analytics/index.php/plus/show',
            urlencode_postdata(data),
            {
                'Origin': 'http://www.dcndigital.ae',
                'Content-Type': 'application/x-www-form-urlencoded'
            })

        show = self._download_json(request, show_id)
        if not season_id:
            season_id = show['default_season']
        for season in show['seasons']:
            if season['id'] == season_id:
                title = season.get('title_en') or season['title_ar']

                entries = []
                for video in show['videos']:
                    video_id = compat_str(video['id'])
                    entries.append(self.url_result(
                        'http://www.dcndigital.ae/media/%s' % video_id, 'DCNVideo', video_id))

                return self.playlist_result(entries, season_id, title)
