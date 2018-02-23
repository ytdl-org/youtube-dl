# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    smuggle_url,
    try_get,
)


class TeleQuebecIE(InfoExtractor):
    _VALID_URL = r'https?://zonevideo\.telequebec\.tv/media/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://zonevideo.telequebec.tv/media/20984/le-couronnement-de-new-york/couronnement-de-new-york',
        'md5': 'fe95a0957e5707b1b01f5013e725c90f',
        'info_dict': {
            'id': '20984',
            'ext': 'mp4',
            'title': 'Le couronnement de New York',
            'description': 'md5:f5b3d27a689ec6c1486132b2d687d432',
            'upload_date': '20170201',
            'timestamp': 1485972222,
        }
    }, {
        # no description
        'url': 'http://zonevideo.telequebec.tv/media/30261',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        media_id = self._match_id(url)
        media_data = self._download_json(
            'https://mnmedias.api.telequebec.tv/api/v2/media/' + media_id,
            media_id)['media']
        return {
            '_type': 'url_transparent',
            'id': media_id,
            'url': smuggle_url(
                'limelight:media:' + media_data['streamInfo']['sourceId'],
                {'geo_countries': ['CA']}),
            'title': media_data['title'],
            'description': try_get(
                media_data, lambda x: x['descriptions'][0]['text'], compat_str),
            'duration': int_or_none(
                media_data.get('durationInMilliseconds'), 1000),
            'ie_key': 'LimelightMedia',
        }


class TeleQuebecLiveIE(InfoExtractor):
    _VALID_URL = r'https?://zonevideo\.telequebec\.tv/(?P<id>endirect)'
    _TEST = {
        'url': 'http://zonevideo.telequebec.tv/endirect/',
        'info_dict': {
            'id': 'endirect',
            'ext': 'mp4',
            'title': 're:^Télé-Québec - En direct [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        m3u8_url = None
        webpage = self._download_webpage(
            'https://player.telequebec.tv/Tq_VideoPlayer.js', video_id,
            fatal=False)
        if webpage:
            m3u8_url = self._search_regex(
                r'm3U8Url\s*:\s*(["\'])(?P<url>(?:(?!\1).)+)\1', webpage,
                'm3u8 url', default=None, group='url')
        if not m3u8_url:
            m3u8_url = 'https://teleqmmd.mmdlive.lldns.net/teleqmmd/f386e3b206814e1f8c8c1c71c0f8e748/manifest.m3u8'
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', m3u8_id='hls')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._live_title('Télé-Québec - En direct'),
            'is_live': True,
            'formats': formats,
        }
