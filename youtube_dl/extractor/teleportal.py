# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    float_or_none,
    parse_iso8601,
    str_or_none,
    str_to_int,
    try_get,
    url_or_none,
)


class TeleportalIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?teleportal\.ua/(?:ua/)?(?P<id>[0-9a-z-]+(?:/[0-9a-z-]+)*)'
    _TEST = {
        'url': 'https://teleportal.ua/ua/show/stb/master-cheff/bitva-sezonov/vypusk-3',
        # no permanent check on file contents as HLS may vary
        'info_dict': {
            'id': 'show/stb/master-cheff/bitva-sezonov/vypusk-3',
            'ext': 'mp4',
            'title': 'МастерШеф. Битва сезонів 3 випуск: найогидніший випуск сезону!',
            'display_id': '2618466',
            'description': 'md5:4179bcc3a12edfa2f655888cd741ac09',
            'timestamp': 1644102480,
            'upload_date': '20220205',
            'thumbnail': r're:^https?://.+\.jpg$',
            'release_timestamp': 1643994000,
            'duration': 11254.0,
            'series_id': '20632',
            'series': 'МастерШеф. Битва сезонів 3 випуск: найогидніший випуск сезону!',
            'season': 'Битва сезонів',
            'episode': 'Найогидніший випуск сезону!',
            'episode_num': 3,
            'categories': ['Шоу'],
        },
        'params': {
            'hls_prefer_native': True,
            # 'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        backend_url = 'https://tp-back.starlight.digital/ua/' + video_id
        series_metadata = self._download_json(backend_url, video_id) or {}
        title = series_metadata['title']
        _hash = series_metadata.get('hash', '')
        api_url = 'https://vcms-api2.starlight.digital/player-api/' + _hash
        api_metadata = self._download_json(
            api_url, video_id,
            query={
                'referer': 'https://teleportal.ua/',
                'lang': 'ua',
            }
        )
        video_info = api_metadata['video'][0]
        formats = []
        for media in ('mediaHlsNoAdv', 'mediaHls'):
            media = url_or_none(try_get(video_info, lambda x: x[media]))
            if not media:
                continue
            formats.extend(self._extract_m3u8_formats(media, video_id, 'mp4', fatal=False))
            break
        self._sort_formats(formats)

        thumbnail = url_or_none(video_info.get('poster'))
        category = series_metadata.get('typeTitle')

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': clean_html(series_metadata.get('description')) or series_metadata.get('seoDescription'),
            'display_id': str_or_none(video_info.get('vcmsId')),
            'hash': _hash,
            'thumbnail': thumbnail,
            'timestamp': parse_iso8601(video_info.get('time_upload_video'), delimiter=' '),
            'release_timestamp': parse_iso8601(video_info.get('publishDate'), delimiter=' '),
            'duration': float_or_none(video_info.get('duration')),
            'series_id': str_or_none(series_metadata.get('id')),
            'series': series_metadata.get('title'),
            'season': video_info.get('seasonName') or series_metadata.get('seasonGallery', {}).get('title'),
            'episode': video_info.get('name'),
            'episode_num': str_to_int(series_metadata.get('seriesTitle')),
            'categories': [category] if category else None,
        }
