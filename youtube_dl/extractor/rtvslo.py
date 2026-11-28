# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    try_get,
    unified_timestamp
)


class RTVSLO4DIE(InfoExtractor):
    _VALID_URL = r'https?://(?:4d\.rtvslo\.si/(?:arhiv/[^/]+|embed)|www\.rtvslo\.si/(?:4d/arhiv|mmr/prispevek))/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://4d.rtvslo.si/arhiv/seje-odbora-za-kmetijstvo-gozdarstvo-in-prehrano/174595438',
        'md5': '37ab1181292a08e0d6b7952545e6ce8b',
        'info_dict': {
            'id': '174595438',
            'ext': 'mp4',
            'title': 'Krajčič o tatvini sendviča',
            'thumbnail': r're:https://img.rtvslo.si/.+\.jpg',
            'timestamp': 1549999614,
            'upload_date': '20190212',
            'duration': 85
        },
    }, {
        'url': 'https://4d.rtvslo.si/arhiv/punto-e-a-capo/174752966',
        'md5': 'a1ce903ee0a4051e417c9357e3d51c71',
        'info_dict': {
            'id': '174752966',
            'ext': 'mp3',
            'title': 'Dante divulgatore della scienza, con Gian Italo Bischi. E un ricordo di Federico Roncoroni',
            'thumbnail': r're:https://img.rtvslo.si/.+\.jpg',
            'timestamp': 1613033635,
            'upload_date': '20210211',
            'duration': 1740
        },
    }, {
        'url': 'https://4d.rtvslo.si/arhiv/punto-e-a-capo/174752966',
        'only_matching': True,
    }, {
        'url': 'https://4d.rtvslo.si/embed/174595438',
        'only_matching': True,
    }, {
        'url': 'https://www.rtvslo.si/4d/arhiv/174752597?s=tv_ita',
        'only_matching': True,
    }, {
        'url': 'https://www.rtvslo.si/mmr/prispevek/174752987',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        media_id = self._match_id(url)

        media_info = self._download_json(
            'https://api.rtvslo.si/ava/getRecording/' + media_id, media_id,
            query={'client_id': '19cc0556a5ee31d0d52a0e30b0696b26'})['response']

        if media_info['mediaType'] == 'video':
            formats = []
            for proto in ('hls_sec', 'hls',):
                formats += self._extract_m3u8_formats(
                    media_info['addaptiveMedia'][proto], media_id, 'mp4',
                    entry_protocol='m3u8_native', m3u8_id='hls')

        elif media_info['mediaType'] == 'audio':
            formats = [{
                'format_id': file['mediaType'],
                'url': file['streamers']['http'] + '/' + file['filename'],
                'ext': determine_ext(file['filename']),
                'tbr': int_or_none(file.get('bitrate')),
                'filesize': int_or_none(file.get('filesize')),
                'vcodec': 'none'
            } for file in media_info['mediaFiles']]

        self._sort_formats(formats)

        return {
            'id': media_id,
            'title': media_info['title'],
            'formats': formats,
            'description': try_get(media_info, 'description'),
            'thumbnail': media_info.get('thumbnail_sec'),
            'timestamp': unified_timestamp(media_info.get('broadcastDate')),
            'duration': media_info.get('duration'),
            'subtitles': self.extract_subtitles(media_info)
        }

    def _get_subtitles(self, media_info):
        subs = {}
        for sub in media_info.get('subtitles', []):
            subs[sub['language']] = [{
                'ext': 'vtt',
                'url': sub['file']
            }]

        return subs
