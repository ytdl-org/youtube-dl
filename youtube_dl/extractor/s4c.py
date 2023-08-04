# coding: utf-8

from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    merge_dicts,
    T,
    traverse_obj,
    txt_or_none,
)


class S4CIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?s4c\.cymru/clic/programme/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.s4c.cymru/clic/programme/861362209',
        'info_dict': {
            'id': '861362209',
            'ext': 'mp4',
            'title': 'Y Swn',
            'description': 'md5:f7681a30e4955b250b3224aa9fe70cf0',
            'duration': 5340
        },
    }, {
        'url': 'https://www.s4c.cymru/clic/programme/856636948',
        'info_dict': {
            'id': '856636948',
            'ext': 'mp4',
            'title': 'Am Dro',
            'duration': 2880,
            'description': 'md5:100d8686fc9a632a0cb2db52a3433ffe',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        details = self._download_json(
            'https://www.s4c.cymru/df/full_prog_details',
            video_id, query={
                'lang': 'e',
                'programme_id': video_id,
            }, fatal=False)

        filename = self._download_json(
            'https://player-api.s4c-cdn.co.uk/player-configuration/prod', video_id, query={
                'programme_id': video_id,
                'signed': '0',
                'lang': 'en',
                'mode': 'od',
                'appId': 'clic',
                'streamName': '',
            }, note='Downloading player config JSON')['filename']
        m3u8_url = self._download_json(
            'https://player-api.s4c-cdn.co.uk/streaming-urls/prod', video_id, query={
                'mode': 'od',
                'application': 'clic',
                'region': 'WW',
                'extra': 'false',
                'thirdParty': 'false',
                'filename': filename,
            }, note='Downloading streaming urls JSON')['hls']
        # ... self._extract_m3u8_formats_and_subtitles(m3u8_url, video_id, 'mp4', m3u8_id='hls')
        formats, subtitles = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', m3u8_id='hls', entry_protocol='m3u8_native'), {}

        return merge_dicts({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
        }, traverse_obj(details, ('full_prog_details', 0, {
            'title': (('programme_title', 'series_title'), T(txt_or_none)),
            'description': ('full_billing', T(txt_or_none)),
            'duration': ('duration', T(lambda x: float_or_none(x, invscale=60))),
        }), get_all=False),
            rev=True)
