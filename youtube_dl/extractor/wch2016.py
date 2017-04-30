# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    int_or_none,
    parse_iso8601,
    parse_duration,
)

class WCH2016IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?wch2016\.com/([^/]+/)*c-(?P<id>\d+)'
    _TESTS = [{
        # type=video
        'url': 'https://www.wch2016.com/video/caneur-best-of-game-2-micd-up/t-281230378/c-44983703',
        'md5': '7ee1069435740c62b6d0cfe9342e1ae0',
        'info_dict': {
            'id': '44983703',
            'ext': 'mp4',
            'title': 'CAN@EUR: Best of Game 2 Mic\'d Up',
            'description': 'Check out the best sounds from Game 2 of the WCH final, as Mic\'d Up takes you through gameplay, as well as Team Canada\'s on ice celebrations',
            'timestamp': 1475273685,
            'upload_date': '20160930',
        }
    },  {
        # type=article
        'url': 'https://www.wch2016.com/news/3-stars-team-europe-vs-team-canada/c-282195068',
        'md5': 'ea056bb6d91c844e60c91a3ff6283f2d',
        'info_dict': {
            'id': '44915203',
            'ext': 'mp4',
            'title': 'EUR@CAN: 3 Stars of the Game',
            'description': 'Tomas Tatar, Patrice Bergeron and Sidney Crosby are your 3 Stars of the Game in Team Canada\'s 3-1 win against Team Europe',
            'timestamp': 1475020800,
            'upload_date': '20160928',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            'https://nhl.bamcontent.com/wch/id/v1/%s/details/web-v1.json' % video_id,
            video_id)

        if video_data.get('type') == 'article':
            video_data = video_data['media']


        video_id = compat_str(video_data['id'])
        title = video_data['title']

        formats = []
        for playback in video_data.get('playbacks', []):
            playback_url = playback.get('url')
            if not playback_url:
                continue
            ext = determine_ext(playback_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    playback_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=playback.get('name', 'hls'), fatal=False))
            else:
                height = int_or_none(playback.get('height'))
                formats.append({
                    'format_id': playback.get('name', 'http' + ('-%dp' % height if height else '')),
                    'url': playback_url,
                    'width': int_or_none(playback.get('width')),
                    'height': height,
                })
        self._sort_formats(formats, ('preference', 'width', 'height', 'tbr', 'format_id'))

        thumbnails = []
        for thumbnail_id, thumbnail_data in video_data.get('image', {}).get('cuts', {}).items():
            thumbnail_url = thumbnail_data.get('src')
            if not thumbnail_url:
                continue
            thumbnails.append({
                'id': thumbnail_id,
                'url': thumbnail_url,
                'width': int_or_none(thumbnail_data.get('width')),
                'height': int_or_none(thumbnail_data.get('height')),
            })

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description'),
            'timestamp': parse_iso8601(video_data.get('date')),
            'duration': parse_duration(video_data.get('duration')),
            'thumbnails': thumbnails,
            'formats': formats,
        }

