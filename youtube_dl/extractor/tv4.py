# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    parse_iso8601,
    try_get,
    determine_ext,
)


class TV4IE(InfoExtractor):
    IE_DESC = 'tv4.se and tv4play.se'
    _VALID_URL = r'''(?x)https?://(?:www\.)?
        (?:
            tv4\.se/(?:[^/]+)/klipp/(?:.*)-|
            tv4play\.se/
            (?:
                (?:program|barn)/(?:[^\?]+)\?video_id=|
                iframe/video/|
                film/|
                sport/|
            )
        )(?P<id>[0-9]+)'''
    _GEO_COUNTRIES = ['SE']
    _TESTS = [
        {
            'url': 'http://www.tv4.se/kalla-fakta/klipp/kalla-fakta-5-english-subtitles-2491650',
            'md5': 'cb837212f342d77cec06e6dad190e96d',
            'info_dict': {
                'id': '2491650',
                'ext': 'mp4',
                'title': 'Kalla Fakta 5 (english subtitles)',
                'thumbnail': r're:^https?://.*\.jpg$',
                'timestamp': int,
                'upload_date': '20131125',
            },
        },
        {
            'url': 'http://www.tv4play.se/iframe/video/3054113',
            'md5': 'cb837212f342d77cec06e6dad190e96d',
            'info_dict': {
                'id': '3054113',
                'ext': 'mp4',
                'title': 'Så här jobbar ficktjuvarna - se avslöjande bilder',
                'thumbnail': r're:^https?://.*\.jpg$',
                'description': 'Unika bilder avslöjar hur turisternas fickor vittjas mitt på Stockholms central. Två experter på ficktjuvarna avslöjar knepen du ska se upp för.',
                'timestamp': int,
                'upload_date': '20150130',
            },
        },
        {
            'url': 'http://www.tv4play.se/sport/3060959',
            'only_matching': True,
        },
        {
            'url': 'http://www.tv4play.se/film/2378136',
            'only_matching': True,
        },
        {
            'url': 'http://www.tv4play.se/barn/looney-tunes?video_id=3062412',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        info = self._download_json(
            'http://www.tv4play.se/player/assets/%s.json' % video_id,
            video_id, 'Downloading video info JSON')

        title = info['title']

        subtitles = {}
        formats = []
        # http formats are linked with unresolvable host
        for kind in ('hls3', ''):
            data = self._download_json(
                'https://prima.tv4play.se/api/web/asset/%s/play.json' % video_id,
                video_id, 'Downloading sources JSON', query={
                    'protocol': kind,
                    'videoFormat': 'MP4+WEBVTT',
                })
            items = try_get(data, lambda x: x['playback']['items']['item'])
            if not items:
                continue
            if isinstance(items, dict):
                items = [items]
            for item in items:
                manifest_url = item.get('url')
                if not isinstance(manifest_url, compat_str):
                    continue
                ext = determine_ext(manifest_url)
                if ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        manifest_url, video_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id=kind, fatal=False))
                elif ext == 'f4m':
                    formats.extend(self._extract_akamai_formats(
                        manifest_url, video_id, {
                            'hls': 'tv4play-i.akamaihd.net',
                        }))
                elif ext == 'webvtt':
                    subtitles = self._merge_subtitles(
                        subtitles, {
                            'sv': [{
                                'url': manifest_url,
                                'ext': 'vtt',
                            }]})

        if not formats and info.get('is_geo_restricted'):
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'description': info.get('description'),
            'timestamp': parse_iso8601(info.get('broadcast_date_time')),
            'duration': int_or_none(info.get('duration')),
            'thumbnail': info.get('image'),
            'is_live': info.get('is_live') is True,
        }
