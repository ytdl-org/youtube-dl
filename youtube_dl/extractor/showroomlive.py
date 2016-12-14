# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError, compat_urlparse


class ShowroomLiveIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?showroom-live\.com/(?P<id>[0-9a-zA-Z_]+)'
    _TEST = {
        'url': 'https://www.showroom-live.com/48_Nana_Okada',
        'skip': 'Only live broadcasts, can\'t predict test case.',
        'info_dict': {
            'id': '48_Nana_Okada',
            'ext': 'mp4',
            'uploader_id': '48_Nana_Okada',
        }
    }

    def _real_extract(self, url):
        broadcaster_id = self._match_id(url)

        # There is no showroom on these pages.
        if broadcaster_id in ['onlive', 'timetable', 'event', 'campaign', 'news', 'ranking']:
            raise ExtractorError('URL %s does not contain a showroom' % url)

        # Retrieve the information we need
        webpage = self._download_webpage(url, broadcaster_id)
        room_id = self._search_regex(r'profile\?room_id\=(\d+)', webpage, 'room_id')
        room_url = compat_urlparse.urljoin(url, "/api/room/profile?room_id=%s") % room_id
        room = self._download_json(room_url, broadcaster_id)

        is_live = room.get('is_onlive')
        if not is_live:
            raise ExtractorError('%s their showroom is not live' % broadcaster_id)

        # Prepare and return the information
        uploader = room.get('performer_name') or broadcaster_id  # performer_name can be an empty string.
        title = room.get('room_name', room.get('main_name', "%s's Showroom" % uploader))

        return {
            'is_live': is_live,
            'id': room.get('live_id'),
            'timestamp': room.get('current_live_started_at'),
            'uploader': uploader,
            'uploader_id': broadcaster_id,
            'title': title,
            'description': room.get('description'),
            'formats': self._extract_formats(url, broadcaster_id, room_id)
        }

    def _extract_formats(self, url, broadcaster_id, room_id):
        formats = []

        stream_url = compat_urlparse.urljoin(url, "/api/live/streaming_url?room_id=%s") % room_id
        streaming_url_list = self._download_json(stream_url, broadcaster_id).get('streaming_url_list', [])

        for stream in streaming_url_list:
            if stream.get('type') == "hls":
                formats.extend(self._extract_m3u8_formats(
                    stream.get('url'),
                    broadcaster_id,
                    ext='mp4',
                    m3u8_id='hls',
                    preference=stream.get('quality', 100) - 10
                ))
            elif stream.get('type') == 'rtmp':
                url = stream.get('url') + '/' + stream.get('stream_name')
                formats.append({
                    'url': url,
                    'format_id': 'rtmp',
                    'protocol': 'rtmp',
                    'ext': 'flv',
                    'preference': stream.get('quality', 100)
                })

        self._sort_formats(formats)
        return formats
