# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_iso8601,
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
    _TESTS = [
        {
            'url': 'http://www.tv4.se/kalla-fakta/klipp/kalla-fakta-5-english-subtitles-2491650',
            'md5': '909d6454b87b10a25aa04c4bdd416a9b',
            'info_dict': {
                'id': '2491650',
                'ext': 'mp4',
                'title': 'Kalla Fakta 5 (english subtitles)',
                'thumbnail': 're:^https?://.*\.jpg$',
                'timestamp': int,
                'upload_date': '20131125',
            },
        },
        {
            'url': 'http://www.tv4play.se/iframe/video/3054113',
            'md5': '77f851c55139ffe0ebd41b6a5552489b',
            'info_dict': {
                'id': '3054113',
                'ext': 'mp4',
                'title': 'Så här jobbar ficktjuvarna - se avslöjande bilder',
                'thumbnail': 're:^https?://.*\.jpg$',
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
            'http://www.tv4play.se/player/assets/%s.json' % video_id, video_id, 'Downloading video info JSON')

        # If is_geo_restricted is true, it doesn't necessarily mean we can't download it
        if info['is_geo_restricted']:
            self.report_warning('This content might not be available in your country due to licensing restrictions.')
        if info['requires_subscription']:
            raise ExtractorError('This content requires subscription.', expected=True)

        sources_data = self._download_json(
            'https://prima.tv4play.se/api/web/asset/%s/play.json?protocol=http&videoFormat=MP4' % video_id, video_id, 'Downloading sources JSON')
        sources = sources_data['playback']

        formats = []
        for item in sources.get('items', {}).get('item', []):
            ext, bitrate = item['mediaFormat'], item['bitrate']
            formats.append({
                'format_id': '%s_%s' % (ext, bitrate),
                'tbr': bitrate,
                'ext': ext,
                'url': item['url'],
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': info['title'],
            'formats': formats,
            'description': info.get('description'),
            'timestamp': parse_iso8601(info.get('broadcast_date_time')),
            'duration': info.get('duration'),
            'thumbnail': info.get('image'),
            'is_live': sources.get('live'),
        }
