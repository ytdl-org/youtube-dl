# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import ExtractorError


class TuneInIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://(?:www\.)?
    (?:
        tunein\.com/
        (?:
            radio/.*?-s|
            station/.*?StationId\=
        )(?P<id>[0-9]+)
        |tun\.in/(?P<redirect_id>[A-Za-z0-9]+)
    )
    '''
    _API_URL_TEMPLATE = 'http://tunein.com/tuner/tune/?stationId={0:}&tuneType=Station'

    _INFO_DICT = {
        'id': '34682',
        'title': 'Jazz 24 on 88.5 Jazz24 - KPLU-HD2',
        'ext': 'aac',
        'thumbnail': 're:^https?://.*\.png$',
        'location': 'Tacoma, WA',
    }
    _TESTS = [
        {
            'url': 'http://tunein.com/radio/Jazz24-885-s34682/',
            'info_dict': _INFO_DICT,
            'params': {
                'skip_download': True,  # live stream
            },
        },
        {  # test redirection
            'url': 'http://tun.in/ser7s',
            'info_dict': _INFO_DICT,
            'params': {
                'skip_download': True,  # live stream
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        redirect_id = mobj.group('redirect_id')
        if redirect_id:
            # The server doesn't support HEAD requests
            urlh = self._request_webpage(
                url, redirect_id, note='Downloading redirect page')
            url = urlh.geturl()
            self.to_screen('Following redirect: %s' % url)
            mobj = re.match(self._VALID_URL, url)
        station_id = mobj.group('id')

        station_info = self._download_json(
            self._API_URL_TEMPLATE.format(station_id),
            station_id, note='Downloading station JSON')

        title = station_info['Title']
        thumbnail = station_info.get('Logo')
        location = station_info.get('Location')
        streams_url = station_info.get('StreamUrl')
        if not streams_url:
            raise ExtractorError('No downloadable streams found',
                                 expected=True)
        stream_data = self._download_webpage(
            streams_url, station_id, note='Downloading stream data')
        streams = json.loads(self._search_regex(
            r'\((.*)\);', stream_data, 'stream info'))['Streams']

        is_live = None
        formats = []
        for stream in streams:
            if stream.get('Type') == 'Live':
                is_live = True
            reliability = stream.get('Reliability')
            format_note = (
                'Reliability: %d%%' % reliability
                if reliability is not None else None)
            formats.append({
                'preference': (
                    0 if reliability is None or reliability > 90
                    else 1),
                'abr': stream.get('Bandwidth'),
                'ext': stream.get('MediaType').lower(),
                'acodec': stream.get('MediaType'),
                'vcodec': 'none',
                'url': stream.get('Url'),
                'source_preference': reliability,
                'format_note': format_note,
            })
        self._sort_formats(formats)

        return {
            'id': station_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'location': location,
            'is_live': is_live,
        }
