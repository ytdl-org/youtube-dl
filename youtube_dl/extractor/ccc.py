from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
)


class CCCIE(InfoExtractor):
    IE_NAME = 'media.ccc.de'
    _VALID_URL = r'https?://(?:www\.)?media\.ccc\.de/v/(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'https://media.ccc.de/v/30C3_-_5443_-_en_-_saal_g_-_201312281830_-_introduction_to_processor_design_-_byterazor#video',
        'md5': '3a1eda8f3a29515d27f5adb967d7e740',
        'info_dict': {
            'id': '1839',
            'ext': 'mp4',
            'title': 'Introduction to Processor Design',
            'description': 'md5:df55f6d073d4ceae55aae6f2fd98a0ac',
            'thumbnail': r're:^https?://.*\.jpg$',
            'upload_date': '20131228',
            'timestamp': 1388188800,
            'duration': 3710,
        }
    }, {
        'url': 'https://media.ccc.de/v/32c3-7368-shopshifting#download',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        event_id = self._search_regex(r"data-id='(\d+)'", webpage, 'event id')
        event_data = self._download_json('https://media.ccc.de/public/events/%s' % event_id, event_id)

        formats = []
        for recording in event_data.get('recordings', []):
            recording_url = recording.get('recording_url')
            if not recording_url:
                continue
            language = recording.get('language')
            folder = recording.get('folder')
            format_id = None
            if language:
                format_id = language
            if folder:
                if language:
                    format_id += '-' + folder
                else:
                    format_id = folder
            vcodec = 'h264' if 'h264' in folder else (
                'none' if folder in ('mp3', 'opus') else None
            )
            formats.append({
                'format_id': format_id,
                'url': recording_url,
                'width': int_or_none(recording.get('width')),
                'height': int_or_none(recording.get('height')),
                'filesize': int_or_none(recording.get('size'), invscale=1024 * 1024),
                'language': language,
                'vcodec': vcodec,
            })
        self._sort_formats(formats)

        return {
            'id': event_id,
            'display_id': display_id,
            'title': event_data['title'],
            'description': event_data.get('description'),
            'thumbnail': event_data.get('thumb_url'),
            'timestamp': parse_iso8601(event_data.get('date')),
            'duration': int_or_none(event_data.get('length')),
            'tags': event_data.get('tags'),
            'formats': formats,
        }
