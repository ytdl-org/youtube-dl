# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    parse_duration,
    parse_iso8601,
    parse_resolution,
    url_or_none,
)


class CCMAIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ccma\.cat/(?:[^/]+/)*?(?P<type>video|audio)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.ccma.cat/tv3/alacarta/lespot-de-la-marato-de-tv3/lespot-de-la-marato-de-tv3/video/5630208/',
        'md5': '7296ca43977c8ea4469e719c609b0871',
        'info_dict': {
            'id': '5630208',
            'ext': 'mp4',
            'title': 'L\'espot de La Marató de TV3',
            'description': 'md5:f12987f320e2f6e988e9908e4fe97765',
            'timestamp': 1470918540,
            'upload_date': '20160811',
        }
    }, {
        'url': 'http://www.ccma.cat/catradio/alacarta/programa/el-consell-de-savis-analitza-el-derbi/audio/943685/',
        'md5': 'fa3e38f269329a278271276330261425',
        'info_dict': {
            'id': '943685',
            'ext': 'mp3',
            'title': 'El Consell de Savis analitza el derbi',
            'description': 'md5:e2a3648145f3241cb9c6b4b624033e53',
            'upload_date': '20171205',
            'timestamp': 1512507300,
        }
    }]

    def _real_extract(self, url):
        media_type, media_id = re.match(self._VALID_URL, url).groups()

        media = self._download_json(
            'http://dinamics.ccma.cat/pvideo/media.jsp', media_id, query={
                'media': media_type,
                'idint': media_id,
            })

        formats = []
        media_url = media['media']['url']
        if isinstance(media_url, list):
            for format_ in media_url:
                format_url = url_or_none(format_.get('file'))
                if not format_url:
                    continue
                label = format_.get('label')
                f = parse_resolution(label)
                f.update({
                    'url': format_url,
                    'format_id': label,
                })
                formats.append(f)
        else:
            formats.append({
                'url': media_url,
                'vcodec': 'none' if media_type == 'audio' else None,
            })
        self._sort_formats(formats)

        informacio = media['informacio']
        title = informacio['titol']
        durada = informacio.get('durada', {})
        duration = int_or_none(durada.get('milisegons'), 1000) or parse_duration(durada.get('text'))
        timestamp = parse_iso8601(informacio.get('data_emissio', {}).get('utc'))

        subtitles = {}
        subtitols = media.get('subtitols', {})
        if subtitols:
            sub_url = subtitols.get('url')
            if sub_url:
                subtitles.setdefault(
                    subtitols.get('iso') or subtitols.get('text') or 'ca', []).append({
                        'url': sub_url,
                    })

        thumbnails = []
        imatges = media.get('imatges', {})
        if imatges:
            thumbnail_url = imatges.get('url')
            if thumbnail_url:
                thumbnails = [{
                    'url': thumbnail_url,
                    'width': int_or_none(imatges.get('amplada')),
                    'height': int_or_none(imatges.get('alcada')),
                }]

        return {
            'id': media_id,
            'title': title,
            'description': clean_html(informacio.get('descripcio')),
            'duration': duration,
            'timestamp': timestamp,
            'thumbnails': thumbnails,
            'subtitles': subtitles,
            'formats': formats,
        }
