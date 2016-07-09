# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import smuggle_url


class FOXIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?fox\.com/watch/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.fox.com/watch/255180355939/7684182528',
        'md5': 'ebd296fcc41dd4b19f8115d8461a3165',
        'info_dict': {
            'id': '255180355939',
            'ext': 'mp4',
            'title': 'Official Trailer: Gotham',
            'description': 'Tracing the rise of the great DC Comics Super-Villains and vigilantes, Gotham reveals an entirely new chapter that has never been told.',
            'duration': 129,
            'timestamp': 1400020798,
            'upload_date': '20140513',
            'uploader': 'NEWA-FNG-FOXCOM',
        },
        'add_ie': ['ThePlatform'],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        release_url = self._parse_json(self._search_regex(
            r'"fox_pdk_player"\s*:\s*({[^}]+?})', webpage, 'fox_pdk_player'),
            video_id)['release_url'] + '&switch=http'

        return {
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'url': smuggle_url(release_url, {'force_smil_url': True}),
            'id': video_id,
        }
