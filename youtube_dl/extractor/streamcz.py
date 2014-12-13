# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
)


class StreamCZIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?stream\.cz/.+/(?P<id>[0-9]+)'

    _TESTS = [{
        'url': 'http://www.stream.cz/peklonataliri/765767-ecka-pro-deti',
        'md5': '6d3ca61a8d0633c9c542b92fcb936b0c',
        'info_dict': {
            'id': '765767',
            'ext': 'mp4',
            'title': 'Peklo na talíři: Éčka pro děti',
            'description': 'Taška s grónskou pomazánkou a další pekelnosti ZDE',
            'thumbnail': 're:^http://im.stream.cz/episode/52961d7e19d423f8f06f0100',
            'duration': 256,
        },
    }, {
        'url': 'http://www.stream.cz/blanik/10002447-tri-roky-pro-mazanka',
        'md5': 'e54a254fb8b871968fd8403255f28589',
        'info_dict': {
            'id': '10002447',
            'ext': 'mp4',
            'title': 'Kancelář Blaník: Tři roky pro Mazánka',
            'description': 'md5:3862a00ba7bf0b3e44806b544032c859',
            'thumbnail': 're:^http://im.stream.cz/episode/537f838c50c11f8d21320000',
            'duration': 368,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            'http://www.stream.cz/API/episode/%s' % video_id, video_id)

        formats = []
        for quality, video in enumerate(data['video_qualities']):
            for f in video['formats']:
                typ = f['type'].partition('/')[2]
                qlabel = video.get('quality_label')
                formats.append({
                    'format_note': '%s-%s' % (qlabel, typ) if qlabel else typ,
                    'format_id': '%s-%s' % (typ, f['quality']),
                    'url': f['source'],
                    'height': int_or_none(f['quality'].rstrip('p')),
                    'quality': quality,
                })
        self._sort_formats(formats)

        image = data.get('image')
        if image:
            thumbnail = self._proto_relative_url(
                image.replace('{width}', '1240').replace('{height}', '697'),
                scheme='http:',
            )
        else:
            thumbnail = None

        stream = data.get('_embedded', {}).get('stream:show', {}).get('name')
        if stream:
            title = '%s: %s' % (stream, data['name'])
        else:
            title = data['name']

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'description': data.get('web_site_text'),
            'duration': int_or_none(data.get('duration')),
            'view_count': int_or_none(data.get('views')),
        }
