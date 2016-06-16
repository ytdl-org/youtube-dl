# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none

import calendar
from datetime import datetime


class PolskieRadioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?polskieradio\.pl/[0-9]+/[0-9]+/Artykul/(?P<id>[0-9]+),.+'
    _TESTS = [{
        'url': 'http://www.polskieradio.pl/7/5102/Artykul/1587943,Prof-Andrzej-Nowak-o-historii-nie-da-sie-myslec-beznamietnie',
        'md5': '2984ee6ce9046d91fc233bc1a864a09a',
        'info_dict': {
            'id': '1587943',
            'ext': 'mp3',
            'title': 'Prof. Andrzej Nowak: o historii nie da się myśleć beznamiętnie',
            'description': 'md5:12f954edbf3120c5e7075e17bf9fc5c5',
            'release_date': '20160227',
            'upload_date': '20160227',
            'timestamp': 1456594200,
            'duration': 2364
        }
    }, {
        'url': 'http://polskieradio.pl/9/305/Artykul/1632955,Bardzo-popularne-slowo-remis',
        'md5': '68a393e25b942c1a76872f56d303a31a',
        'info_dict': {
            'id': '1632955',
            'ext': 'mp3',
            'title': 'Bardzo popularne słowo: remis',
            'description': 'md5:3b58dfae614100abc0f175a0b26d5680',
            'release_date': '20160617',
            'upload_date': '20160617',
            'timestamp': 1466184900,
            'duration': 393
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        metadata_string = self._html_search_regex(r'<span class="play pr-media-play" data-media=(\{.+\})>', webpage, 'metadata')
        metadata = self._parse_json(metadata_string, video_id)

        title = self._og_search_title(webpage)
        if title is not None:
            title = title.strip()

        description = self._og_search_description(webpage)
        if description is not None:
            description = description.strip()

        release_date = self._html_search_regex(r'Data emisji:[^0-9]+([0-9]{1,2}\.[0-9]{2}\.[0-9]{4})', webpage, 'release date', fatal=False)
        if release_date is not None:
            release_date = datetime.strptime(release_date, '%d.%m.%Y').strftime('%Y%m%d')

        upload_datetime = self._html_search_regex(r'<span id="datetime2" class="time">\s+(.+)\s+</span>', webpage, 'release time', fatal=False)
        if upload_datetime is not None:
            timestamp = calendar.timegm(datetime.strptime(upload_datetime, '%d.%m.%Y %H:%M').timetuple())
        else:
            timestamp = None

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'display_id': metadata.get('id'),
            'duration': int_or_none(metadata.get('length')),
            'url': self._proto_relative_url(metadata.get('file'), 'http:'),
            'release_date': release_date,
            'timestamp': timestamp
        }
