# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import qualities


class SzenikEUIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?szenik\.eu/(?:de|fr)/Szenik-live/(?P<genre>[^/]+)/(?P<id>[^.]+)'
    _TEST = {
        'url': 'http://www.szenik.eu/fr/Szenik-live/Classique/Frozen-in-Time-bw0Y9lgV47.html',
        'md5': 'ee7bf216459292ca00237610d9de6876',
        'info_dict': {
            'id': 'Frozen-in-Time-bw0Y9lgV47',
            'ext': 'mp4',
            'title': 'Frozen in Time',
            'description': 'Le Tonhalle-Orchester de Zurich et la star des percussionnistes Martin Grubinger jouent Frozen in Time d’Avner Dorman et Le Sacre du printemps de Stravinski. Un concert à revoir en intégralité sur szenik Live.',
            'thumbnail': 'http://www.szenik.eu/videoimages/grand/Tonhalle_Frozen_in_time.jpg',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_meta('og:title', webpage)
        title = title.split(' |')[0]
        thumbnail = self._html_search_meta('og:image', webpage)
        description = self._html_search_meta('og:description', webpage, fatal=False)

        # The folder name is obtained from the image thumbnail
        video_folder = thumbnail.rsplit('/', 1)[1].split('.')[0]
        baseurl = 'http://vod.szenik.eu:8134/media/szenik/%s/' % video_folder

        m3u8_url = baseurl + 'index.m3u8'
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')

        QUALITIES = ('low', 'med', 'high')
        quality = qualities(QUALITIES)

        for q in QUALITIES:
            formats.append({
                'format_id': q,
                'quality': quality(q),
                'url': baseurl + q + '.mp4',
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'description': description,
            'formats': formats,
        }
