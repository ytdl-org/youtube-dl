# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    smuggle_url,
)


class TVAIE(InfoExtractor):
    _VALID_URL = r'https?://videos\.tva\.ca/details/_(?P<id>\d+)'
    _TEST = {
        'url': 'https://videos.tva.ca/details/_5596811470001',
        'info_dict': {
            'id': '5596811470001',
            'ext': 'mp4',
            'title': 'Un extrait de l\'épisode du dimanche 8 octobre 2017 !',
            'uploader_id': '5481942443001',
            'upload_date': '20171003',
            'timestamp': 1507064617,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/5481942443001/default_default/index.html?videoId=%s'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            'https://videos.tva.ca/proxy/item/_' + video_id, video_id, headers={
                'Accept': 'application/json',
            }, query={
                'appId': '5955fc5f23eec60006c951f1',
            })

        def get_attribute(key):
            for attribute in video_data.get('attributes', []):
                if attribute.get('key') == key:
                    return attribute.get('value')
            return None

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'title': get_attribute('title'),
            'url': smuggle_url(self.BRIGHTCOVE_URL_TEMPLATE % video_id, {'geo_countries': ['CA']}),
            'description': get_attribute('description'),
            'thumbnail': get_attribute('image-background') or get_attribute('image-landscape'),
            'duration': float_or_none(get_attribute('video-duration'), 1000),
            'ie_key': 'BrightcoveNew',
        }
