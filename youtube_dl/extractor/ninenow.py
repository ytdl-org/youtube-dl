# coding: utf-8
from __future__ import unicode_literals

from datetime import datetime

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    int_or_none,
    float_or_none,
    smuggle_url,
)


class NineNowIE(InfoExtractor):
    IE_NAME = '9now.com.au'
    _VALID_URL = r'https?://(?:www\.)?9now\.com\.au/(?:[^/]+/){2}(?P<id>[^/?#]+)'
    _GEO_COUNTRIES = ['AU']

    # Deprecated these tests as of 2021-04-22 as these files no longer exist (404) but
    #  the structure may be of future use.
    #
    # _TESTS = [
    #     # clip
    #     'url': 'https://www.9now.com.au/afl-footy-show/2016/clip-ciql02091000g0hp5oktrnytc',
    #     'md5': '17cf47d63ec9323e562c9957a968b565',
    #     'info_dict': {
    #         'id': '16801',
    #         'ext': 'mp4',
    #         'title': 'St. Kilda\'s Joey Montagna on the potential for a player\'s strike',
    #         'description': 'Is a boycott of the NAB Cup "on the table"?',
    #         'uploader_id': '4460760524001',
    #         'upload_date': '20160713',
    #         'timestamp': 1468421266,
    #     },
    #     # 'skip': 'Only available in Australia',
    # }, {
    #     # episode
    #     'url': 'https://www.9now.com.au/afl-footy-show/2016/episode-19',
    #     'only_matching': True,
    # }, {
    #     # DRM protected
    #     'url': 'https://www.9now.com.au/andrew-marrs-history-of-the-world/season-1/episode-1',
    #     'only_matching': True,
    # },

    _TESTS = [{
        # episode of series
        'url': 'https://www.9now.com.au/lego-masters/season-3/episode-3',
        'md5': 'e73b986e7efb81c90896f0806e56d7e4',
        'info_dict': {
            'id': '6249614030001',
            'title': "Episode 3",
            'ext': 'mp4',
            'season_number': 3,
            'episode_number': 3,
            'description': 'In the first elimination of the competition, teams will have 10 hours to build a world inside a snow globe.',
            'uploader_id': "4460760524001",
            'timestamp': 1618966200.0,
            'upload_date': "20210421",
        },
        'only_matching': False,
    }]
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/4460760524001/default_default/index.html?videoId=%s'

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        # import pdb; pdb.set_trace()
        page_data = self._parse_json(
            self._search_regex(
                r'window\.__data\s*=\s*({.*?});',
                webpage,
                'page data',
                default='{}'
            ),
            display_id,
            fatal=False
        )
        if not page_data:
            page_data = self._parse_json(self._parse_json(self._search_regex(
                r'window\.__data\s*=\s*JSON\.parse\s*\(\s*(".+?")\s*\)\s*;',
                webpage, 'page data'), display_id), display_id)

        for kind in ('episode', 'clip'):
            current_key = page_data.get(kind, {}).get(
                'current%sKey' % kind.capitalize())
            if not current_key:
                continue
            cache = page_data.get(kind, {}).get('%sCache' % kind, {})
            if not cache:
                continue
            common_data = {
                'episode': (cache.get(current_key) or list(cache.values())[0])[kind],
                'season': (cache.get(current_key) or list(cache.values())[0]).get('season', None)
            }
            break
        else:
            raise ExtractorError('Unable to find video data')

        video_data = common_data['episode']['video']

        if video_data.get('drm'):
            raise ExtractorError('This video is DRM protected.', expected=True)

        brightcove_id = video_data.get('brightcoveId') or 'ref:' + video_data['referenceId']
        video_id = compat_str(video_data.get('id') or brightcove_id)
        title = common_data['episode']['name']
        season_number = common_data.get("season").get("seasonNumber", None)
        episode_number = common_data.get('episode').get("episodeNumber", None)
        timestamp = None
        upload_date = None

        for key in ('airDate', 'availability'):
            if key in common_data.get("episode"):
                parsed_datetime = datetime.strptime(common_data.get('episode').get("airDate"), "%Y-%m-%dT%H:%M:%S.000Z")
                if key == 'airDate':
                    timestamp = parsed_datetime.timestamp()

                if key == 'availability':
                    upload_date = parsed_datetime.strftime("%Y%m%d")

        thumbnails = [{
            'id': thumbnail_id,
            'url': thumbnail_url,
            'width': int_or_none(thumbnail_id[1:])
        } for thumbnail_id, thumbnail_url in common_data.get('episode').get('image', {}).get('sizes', {}).items()]

        return {
            '_type': 'url_transparent',
            'url': smuggle_url(
                self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id,
                {'geo_countries': self._GEO_COUNTRIES}),
            'id': video_id,
            'title': title,
            'description': common_data.get('episode').get('description'),
            'duration': float_or_none(video_data.get('duration'), 1000),
            'thumbnails': thumbnails,
            'ie_key': 'BrightcoveNew',
            'season_number': season_number,
            'episode_number': episode_number,
            "timestamp": timestamp,
            "upload_date": upload_date,
        }
