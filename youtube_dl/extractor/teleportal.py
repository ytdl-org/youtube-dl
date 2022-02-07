# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class TeleportalIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?teleportal\.ua(/ua)?/(?P<id>[0-9a-z-/]+)'
    _TEST = {
        'url': 'https://teleportal.ua/ua/show/stb/master-cheff/bitva-sezonov/vypusk-3',
        'md5': '07bd056c45b515fa9cc0202b8403df41',
        'info_dict': {
            'id': 'show/stb/master-cheff/bitva-sezonov/vypusk-3',
            'ext': 'mp4',
            'title': 'МастерШеф. Битва сезонів 3 випуск: найогидніший випуск сезону!',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': r're:^<p>Не пропустіть.*',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        backend_url = 'https://tp-back.starlight.digital/ua/{}'.format(video_id)
        metadata = self._download_json(backend_url, video_id)
        api_metadata = self._download_json('https://vcms-api2.starlight.digital/player-api/{}?referer=https://teleportal.ua/&lang=ua'.format(metadata["hash"]), video_id)

        return {
            'id': video_id,
            'title': metadata['title'],
            'description': metadata['description'],
            'real_id': metadata['id'],
            'hash': metadata['hash'],
            'url': api_metadata['video'][0]['mediaHls'],
            'thumbnail': api_metadata['video'][0]['poster'],
            'formats': self._extract_m3u8_formats(api_metadata['video'][0]['mediaHls'], video_id, 'mp4'),
        }
