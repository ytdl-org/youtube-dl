# coding: utf-8
from __future__ import unicode_literals

from .adobepass import AdobePassIE
from ..utils import (
    update_url_query,
    extract_attributes,
    parse_age_limit,
    smuggle_url,
)


class FXNetworksIE(AdobePassIE):
    _VALID_URL = r'https?://(?:www\.)?(?:fxnetworks|simpsonsworld)\.com/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.fxnetworks.com/video/1046477891799',
        'md5': 'b5d9896b224e6c85f10e92fbac3a9115',
        'info_dict': {
            'id': '1046477891799',
            'ext': 'mp4',
            'title': 'September',
            'description': 'Sam has people over. An FX Original Series, Thursday 10PM on FX.',
            'age_limit': 14,
            'uploader': 'NEWA-FNG-FX',
            'upload_date': '20170615',
            'timestamp': 1505453400,
            'episode_number': 1,
            'season_number': 2,
            'series': 'Better Things',
            
        },
        'add_ie': ['ThePlatform'],
    }, {
        'url': 'http://www.simpsonsworld.com/video/716094019682',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        if 'The content you are trying to access is not available in your region.' in webpage:
            self.raise_geo_restricted()
        video_data = extract_attributes(self._search_regex(
            r'(<a.+?rel="http://link\.theplatform\.com/s/.+?</a>)', webpage, 'video data'))
        player_type = self._search_regex(r'playerType\s*=\s*[\'"]([^\'"]+)', webpage, 'player type', default=None)
        release_url = video_data['rel']
        title = video_data['data-title']
        rating = video_data.get('data-rating')
        query = {
            'mbr': 'true',
        }
        if player_type == 'movies':
            query.update({
                'manifest': 'm3u',
            })
        else:
            query.update({
                'switch': 'http',
            })
        if video_data.get('data-req-auth') == '1':
            resource = self._get_mvpd_resource(
                video_data['data-channel'], title,
                video_data.get('data-guid'), rating)
            query['auth'] = self._extract_mvpd_auth(url, video_id, 'fx', resource)

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'title': title,
            'url': smuggle_url(update_url_query(release_url, query), {'force_smil_url': True}),
            'series': video_data.get('data-show-title'),
            'episode_number': int_or_none(video_data.get('data-episode')),
            'season_number': int_or_none(video_data.get('data-season')),
            'thumbnail': video_data.get('data-large-thumb'),
            'age_limit': parse_age_limit(rating),
            'ie_key': 'ThePlatform',
        }
