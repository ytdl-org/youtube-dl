# coding: utf-8
from __future__ import unicode_literals

from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    smuggle_url,
    try_get,
)


class NoovoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?noovo\.ca/videos/(?P<id>[^/]+/[^/?#&]+)'
    _TESTS = [{
        # clip
        'url': 'http://noovo.ca/videos/rpm-plus/chrysler-imperial',
        'info_dict': {
            'id': '5386045029001',
            'ext': 'mp4',
            'title': 'Chrysler Imperial',
            'description': 'md5:de3c898d1eb810f3e6243e08c8b4a056',
            'timestamp': 1491399228,
            'upload_date': '20170405',
            'uploader_id': '618566855001',
            'creator': 'vtele',
            'view_count': int,
            'series': 'RPM+',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # episode
        'url': 'http://noovo.ca/videos/l-amour-est-dans-le-pre/episode-13-8',
        'info_dict': {
            'id': '5395865725001',
            'title': 'Épisode 13 : Les retrouvailles',
            'description': 'md5:336d5ebc5436534e61d16e63ddfca327',
            'ext': 'mp4',
            'timestamp': 1492019320,
            'upload_date': '20170412',
            'uploader_id': '618566855001',
            'creator': 'vtele',
            'view_count': int,
            'series': "L'amour est dans le pré",
            'season_number': 5,
            'episode': 'Épisode 13',
            'episode_number': 13,
        },
        'params': {
            'skip_download': True,
        },
    }]
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/618566855001/default_default/index.html?videoId=%s'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        data = self._download_json(
            'http://api.noovo.ca/api/v1/pages/single-episode/%s' % video_id,
            video_id)['data']

        content = try_get(data, lambda x: x['contents'][0])

        brightcove_id = data.get('brightcoveId') or content['brightcoveId']

        series = try_get(
            data, (
                lambda x: x['show']['title'],
                lambda x: x['season']['show']['title']),
            compat_str)

        episode = None
        og = data.get('og')
        if isinstance(og, dict) and og.get('type') == 'video.episode':
            episode = og.get('title')

        video = content or data

        return {
            '_type': 'url_transparent',
            'ie_key': BrightcoveNewIE.ie_key(),
            'url': smuggle_url(
                self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id,
                {'geo_countries': ['CA']}),
            'id': brightcove_id,
            'title': video.get('title'),
            'creator': video.get('source'),
            'view_count': int_or_none(video.get('viewsCount')),
            'series': series,
            'season_number': int_or_none(try_get(
                data, lambda x: x['season']['seasonNumber'])),
            'episode': episode,
            'episode_number': int_or_none(data.get('episodeNumber')),
        }
