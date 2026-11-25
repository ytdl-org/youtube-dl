# coding: utf-8
from __future__ import unicode_literals

import re
import calendar
from datetime import datetime
import time

from .common import InfoExtractor

from ..compat import compat_str
from ..utils import (
    clean_html,
    determine_ext,
    extract_attributes,
    ExtractorError,
    get_elements_by_class,
    HEADRequest,
    parse_duration,
    try_get,
    unified_timestamp,
    url_or_none,
    urljoin,
)


class TalkTVIE(InfoExtractor):
    IE_NAME = 'talk.tv'
    IE_DESC = 'TalkTV UK catch-up and live shows'
    _VALID_URL = r'https?://watch\.talk\.tv/(?P<id>watch/(?:vod|replay)/\d+|live)'
    _TESTS = [{
        'url': 'https://watch.talk.tv/watch/replay/12216792',
        'md5': 'dc9071f7d26f48ce4057a98425894eb3',
        'info_dict': {
            'id': '12216792',
            'ext': 'mp4',
            'title': 'Piers Morgan Uncensored',
            'description': 'The host interviews former US President Donald Trump',
            'timestamp': 1650917390,
            'upload_date': '20220425',
            'duration': float,
        },
        'params': {
            'skip_download': True,  # adaptive download
        },
    }, {
        'url': 'https://watch.talk.tv/live',
        'info_dict': {
            'id': 'live',
            'ext': 'mp4',
            'title': 'Piers Morgan Uncensored',
            'description': compat_str,
            'timestamp': int,
            # needs core fix to force compat_str type
            'upload_date': r're:\d{8}',
            'duration': float,
        },
        'params': {
            'skip_download': True,
        },
    },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url).rsplit('/', 1)[-1]
        is_live = (video_id == 'live')
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'(?is)<h1\b[^>]+>\s*(.+?)\s*</h1', webpage, 'title')
        player = self._search_regex(r'''(<[dD][iI][vV]\b[^>]+?\bid\s*=\s*(?P<q>"|')player(?P=q)[^>]*>)''', webpage, video_id)
        player = extract_attributes(player)
        expiry = player.get('expiry')
        if expiry is not None and expiry < time.time():
            raise ExtractorError('Video has expired', expected=True)
        api_info = self._download_json(
            'https://mm-v2.simplestream.com/ssmp/api.php?id=%(data-id)s&env=%(data-env)s' % player,
            video_id, note='Downloading API info', fatal=False)
        player['api_url'] = (
            url_or_none(try_get(api_info, lambda x: x['response']['api_hostname']))
            or 'https://v2-streams-elb.simplestreamcdn.com')
        headers = {'Referer': url, }
        for item in ('uvid', 'token', ('expiry', 'Token-Expiry')):
            if isinstance(item, compat_str):
                name = item.capitalize()
            else:
                item, name = item
            val = player.get('data-' + item)
            if val is not None:
                headers[name] = val

        stream_info = self._download_json(
            '%(api_url)s/api/%(data-type)s/stream/%(data-uvid)s?key=%(data-key)s&platform=firefox&cc=%(data-country)s' % player,
            video_id, headers=headers)
        error = try_get(stream_info, lambda x: x['response']['error'])
        if error:
            raise ExtractorError('Streaming API reported: ' + error, expected=True)
        fmt_url = (stream_info['response'].get('drm') in (None, False)) and stream_info['response']['stream']
        formats = []
        duration = None
        description = None
        timestamp = None
        if fmt_url:
            ext = determine_ext(fmt_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    fmt_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', live=is_live, fatal=False))
            elif ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    fmt_url, video_id, mpd_id='dash', live=is_live, fatal=False))
            else:
                formats.append({
                    'url': fmt_url,
                })
            if not is_live:
                res = self._request_webpage(HEADRequest(fmt_url), video_id, note='Checking date', fatal=False)
                if res is not False:
                    timestamp = unified_timestamp(res.info().getheader('last-modified'))

        self._sort_formats(formats)

        text_fields = get_elements_by_class('text-start', webpage)
        for text in text_fields:
            text = clean_html(text)
            if text.startswith('EPISODE'):
                duration = parse_duration(
                    self._html_search_regex(r'^EPISODE\b\W*(\w[\w\s]*?)\s*$', text, 'duration', default=None))
            elif text.startswith('Live'):
                duration = self._html_search_regex(r'^Live\b(?:<[^>]+>|\W)*([0-2]?\d:\d{2}\s*-\s*[0-2]?\d:\d{2})\s*$', text, 'duration', default=None)
                duration = list(map(lambda x: datetime.strptime(x, '%H:%M'), re.split(r'\s*-\s*', duration)))
                if None not in duration and len(duration) == 2:
                    timestamp = datetime.now().replace(hour=duration[0].hour, minute=duration[0].minute, second=0, microsecond=0)
                    timestamp = calendar.timegm(timestamp.timetuple())
                    duration = duration[1] - duration[0]
                    try:
                        duration = duration.total_seconds()
                    except AttributeError:
                        # Py 2.6
                        duration = duration.td_seconds
                    if duration is not None and duration < 0:
                        duration += 24 * 3600
            else:
                description = text

        return {
            # ensure live has a fixed ID
            'id': player['data-uvid'] if not is_live else video_id,
            'title': title,
            'display_id': video_id if not is_live else player['data-uvid'],
            'formats': formats,
            'thumbnail': player.get('data-poster'),
            'duration': duration,
            'timestamp': timestamp,
            'description': description,
            'is_live': is_live,
        }


class TalkTVSeriesIE(InfoExtractor):
    IE_NAME = 'talk.tv:series'
    IE_DESC = 'TalkTV UK series catch-up'
    _VALID_URL = r'https?://(?:watch\.|www\.)?talk\.tv/shows/(?P<id>[\da-f]{8}-(?:[\da-f]{4}-){3}[\da-f]{12})'
    _TESTS = [{
        'url': 'https://watch.talk.tv/shows/86dadc3e-c4d2-11ec-b4c6-0af62ebc70d1',
        'info_dict': {
            'id': '86dadc3e-c4d2-11ec-b4c6-0af62ebc70d1',
        },
        'playlist_mincount': 4,
    },
    ]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        episodes = re.finditer(
            r'''(?i)<a\b[^>]+?\bhref\s*=\s*(?P<q>"|')(?P<href>/watch/(?:(?!(?P=q)).)+)(?P=q)''',
            webpage)
        return self.playlist_from_matches(
            episodes, playlist_id, getter=lambda x: urljoin(url, x.group('href')), ie='TalkTV')
