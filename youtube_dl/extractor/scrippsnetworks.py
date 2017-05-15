# coding: utf-8
from __future__ import unicode_literals

from .adobepass import AdobePassIE
from ..utils import (
    int_or_none,
    smuggle_url,
    update_url_query,
)


class ScrippsNetworksWatchIE(AdobePassIE):
    IE_NAME = 'scrippsnetworks:watch'
    _VALID_URL = r'https?://watch\.(?:hgtv|foodnetwork|travelchannel|diynetwork|cookingchanneltv)\.com/player\.[A-Z0-9]+\.html#(?P<id>\d+)'
    _TEST = {
        'url': 'http://watch.hgtv.com/player.HNT.html#0256538',
        'md5': '26545fd676d939954c6808274bdb905a',
        'info_dict': {
            'id': '0256538',
            'ext': 'mp4',
            'title': 'Seeking a Wow House',
            'description': 'Buyers retiring in Palm Springs, California, want a modern house with major wow factor. They\'re also looking for a pool and a large, open floorplan with tall windows looking out at the views.',
            'uploader': 'SCNI',
            'upload_date': '20170207',
            'timestamp': 1486450493,
        },
        'skip': 'requires TV provider authentication',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        channel = self._parse_json(self._search_regex(
            r'"channels"\s*:\s*(\[.+\])',
            webpage, 'channels'), video_id)[0]
        video_data = next(v for v in channel['videos'] if v.get('nlvid') == video_id)
        title = video_data['title']
        release_url = video_data['releaseUrl']
        if video_data.get('restricted'):
            requestor_id = self._search_regex(
                r'requestorId\s*=\s*"([^"]+)";', webpage, 'requestor id')
            resource = self._get_mvpd_resource(
                requestor_id, title, video_id,
                video_data.get('ratings', [{}])[0].get('rating'))
            auth = self._extract_mvpd_auth(
                url, video_id, requestor_id, resource)
            release_url = update_url_query(release_url, {'auth': auth})

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'title': title,
            'url': smuggle_url(release_url, {'force_smil_url': True}),
            'description': video_data.get('description'),
            'thumbnail': video_data.get('thumbnailUrl'),
            'series': video_data.get('showTitle'),
            'season_number': int_or_none(video_data.get('season')),
            'episode_number': int_or_none(video_data.get('episodeNumber')),
            'ie_key': 'ThePlatform',
        }
