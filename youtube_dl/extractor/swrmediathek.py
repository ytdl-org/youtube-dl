# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import parse_duration


class SWRMediathekIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?swrmediathek\.de/(?:content/)?player\.htm\?show=(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})'

    _TESTS = [{
        'url': 'http://swrmediathek.de/player.htm?show=849790d0-dab8-11e3-a953-0026b975f2e6',
        'md5': '8c5f6f0172753368547ca8413a7768ac',
        'info_dict': {
            'id': '849790d0-dab8-11e3-a953-0026b975f2e6',
            'ext': 'mp4',
            'title': 'SWR odysso',
            'description': 'md5:2012e31baad36162e97ce9eb3f157b8a',
            'thumbnail': 're:^http:.*\.jpg$',
            'duration': 2602,
            'upload_date': '20140515',
            'uploader': 'SWR Fernsehen',
            'uploader_id': '990030',
        },
    }, {
        'url': 'http://swrmediathek.de/player.htm?show=0e1a8510-ddf2-11e3-9be3-0026b975f2e6',
        'md5': 'b10ab854f912eecc5a6b55cd6fc1f545',
        'info_dict': {
            'id': '0e1a8510-ddf2-11e3-9be3-0026b975f2e6',
            'ext': 'mp4',
            'title': 'Nachtcafé - Alltagsdroge Alkohol - zwischen Sektempfang und Komasaufen',
            'description': 'md5:e0a3adc17e47db2c23aab9ebc36dbee2',
            'thumbnail': 're:http://.*\.jpg',
            'duration': 5305,
            'upload_date': '20140516',
            'uploader': 'SWR Fernsehen',
            'uploader_id': '990030',
        },
    }, {
        'url': 'http://swrmediathek.de/player.htm?show=bba23e10-cb93-11e3-bf7f-0026b975f2e6',
        'md5': '4382e4ef2c9d7ce6852535fa867a0dd3',
        'info_dict': {
            'id': 'bba23e10-cb93-11e3-bf7f-0026b975f2e6',
            'ext': 'mp3',
            'title': 'Saša Stanišic: Vor dem Fest',
            'description': 'md5:5b792387dc3fbb171eb709060654e8c9',
            'thumbnail': 're:http://.*\.jpg',
            'duration': 3366,
            'upload_date': '20140520',
            'uploader': 'SWR 2',
            'uploader_id': '284670',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        video = self._download_json(
            'http://swrmediathek.de/AjaxEntry?ekey=%s' % video_id, video_id, 'Downloading video JSON')

        attr = video['attr']
        media_type = attr['entry_etype']

        formats = []
        for entry in video['sub']:
            if entry['name'] != 'entry_media':
                continue

            entry_attr = entry['attr']
            codec = entry_attr['val0']
            quality = int(entry_attr['val1'])

            fmt = {
                'url': entry_attr['val2'],
                'quality': quality,
            }

            if media_type == 'Video':
                fmt.update({
                    'format_note': ['144p', '288p', '544p', '720p'][quality - 1],
                    'vcodec': codec,
                })
            elif media_type == 'Audio':
                fmt.update({
                    'acodec': codec,
                })
            formats.append(fmt)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': attr['entry_title'],
            'description': attr['entry_descl'],
            'thumbnail': attr['entry_image_16_9'],
            'duration': parse_duration(attr['entry_durat']),
            'upload_date': attr['entry_pdatet'][:-4],
            'uploader': attr['channel_title'],
            'uploader_id': attr['channel_idkey'],
            'formats': formats,
        }
