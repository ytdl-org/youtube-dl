# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class TouTvIE(InfoExtractor):
    IE_NAME = 'tou.tv'
    _VALID_URL = r'https?://ici\.tou\.tv/(?P<id>[a-zA-Z0-9_-]+/S[0-9]+E[0-9]+)'

    _TEST = {
        'url': 'http://ici.tou.tv/garfield-tout-court/S2015E17',
        'info_dict': {
            'id': '122017',
            'ext': 'mp4',
            'title': 'Saison 2015 Épisode 17',
            'description': 'La photo de famille 2',
            'upload_date': '20100717',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        path = self._match_id(url)
        metadata = self._download_json('http://ici.tou.tv/presentation/%s' % path, path)
        video_id = metadata['IdMedia']
        details = metadata['Details']
        title = details['OriginalTitle']

        return {
            '_type': 'url_transparent',
            'url': 'radiocanada:%s:%s' % (metadata.get('AppCode', 'toutv'), video_id),
            'id': video_id,
            'title': title,
            'thumbnail': details.get('ImageUrl'),
            'duration': int_or_none(details.get('LengthInSeconds')),
        }
