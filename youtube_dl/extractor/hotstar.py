# coding: utf-8
from __future__ import unicode_literals

import hashlib
import hmac
import time
import uuid

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_str,
)
from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    str_or_none,
    try_get,
    url_or_none,
)


class HotStarBaseIE(InfoExtractor):
    _AKAMAI_ENCRYPTION_KEY = b'\x05\xfc\x1a\x01\xca\xc9\x4b\xc4\x12\xfc\x53\x12\x07\x75\xf9\xee'

    def _call_api_impl(self, path, video_id, query):
        st = int(time.time())
        exp = st + 6000
        auth = 'st=%d~exp=%d~acl=/*' % (st, exp)
        auth += '~hmac=' + hmac.new(self._AKAMAI_ENCRYPTION_KEY, auth.encode(), hashlib.sha256).hexdigest()
        response = self._download_json(
            'https://api.hotstar.com/' + path, video_id, headers={
                'hotstarauth': auth,
                'x-country-code': 'IN',
                'x-platform-code': 'JIO',
            }, query=query)
        if response['statusCode'] != 'OK':
            raise ExtractorError(
                response['body']['message'], expected=True)
        return response['body']['results']

    def _call_api(self, path, video_id, query_name='contentId'):
        return self._call_api_impl(path, video_id, {
            query_name: video_id,
            'tas': 10000,
        })

    def _call_api_v2(self, path, video_id):
        return self._call_api_impl(
            '%s/in/contents/%s' % (path, video_id), video_id, {
                'desiredConfig': 'encryption:plain;ladder:phone,tv;package:hls,dash',
                'client': 'mweb',
                'clientVersion': '6.18.0',
                'deviceId': compat_str(uuid.uuid4()),
                'osName': 'Windows',
                'osVersion': '10',
            })


class HotStarIE(HotStarBaseIE):
    IE_NAME = 'hotstar'
    _VALID_URL = r'https?://(?:www\.)?hotstar\.com/(?:.+?[/-])?(?P<id>\d{10})'
    _TESTS = [{
        # contentData
        'url': 'https://www.hotstar.com/can-you-not-spread-rumours/1000076273',
        'info_dict': {
            'id': '1000076273',
            'ext': 'mp4',
            'title': 'Can You Not Spread Rumours?',
            'description': 'md5:c957d8868e9bc793ccb813691cc4c434',
            'timestamp': 1447248600,
            'upload_date': '20151111',
            'duration': 381,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        # contentDetail
        'url': 'https://www.hotstar.com/movies/radha-gopalam/1000057157',
        'only_matching': True,
    }, {
        'url': 'http://www.hotstar.com/sports/cricket/rajitha-sizzles-on-debut-with-329/2001477583',
        'only_matching': True,
    }, {
        'url': 'http://www.hotstar.com/1000000515',
        'only_matching': True,
    }, {
        # only available via api v2
        'url': 'https://www.hotstar.com/tv/ek-bhram-sarvagun-sampanna/s-2116/janhvi-targets-suman/1000234847',
        'only_matching': True,
    }]
    _GEO_BYPASS = False

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        app_state = self._parse_json(self._search_regex(
            r'<script>window\.APP_STATE\s*=\s*({.+?})</script>',
            webpage, 'app state'), video_id)
        video_data = {}
        getters = list(
            lambda x, k=k: x['initialState']['content%s' % k]['content']
            for k in ('Data', 'Detail')
        )
        for v in app_state.values():
            content = try_get(v, getters, dict)
            if content and content.get('contentId') == video_id:
                video_data = content
                break

        title = video_data['title']

        if video_data.get('drmProtected'):
            raise ExtractorError('This video is DRM protected.', expected=True)

        formats = []
        geo_restricted = False
        playback_sets = self._call_api_v2('h/v2/play', video_id)['playBackSets']
        for playback_set in playback_sets:
            if not isinstance(playback_set, dict):
                continue
            format_url = url_or_none(playback_set.get('playbackUrl'))
            if not format_url:
                continue
            tags = str_or_none(playback_set.get('tagsCombination')) or ''
            if tags and 'encryption:plain' not in tags:
                continue
            ext = determine_ext(format_url)
            try:
                if 'package:hls' in tags or ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        format_url, video_id, 'mp4', m3u8_id='hls'))
                elif 'package:dash' in tags or ext == 'mpd':
                    formats.extend(self._extract_mpd_formats(
                        format_url, video_id, mpd_id='dash'))
                elif ext == 'f4m':
                    # produce broken files
                    pass
                else:
                    formats.append({
                        'url': format_url,
                        'width': int_or_none(playback_set.get('width')),
                        'height': int_or_none(playback_set.get('height')),
                    })
            except ExtractorError as e:
                if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                    geo_restricted = True
                continue
        if not formats and geo_restricted:
            self.raise_geo_restricted(countries=['IN'])
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description'),
            'duration': int_or_none(video_data.get('duration')),
            'timestamp': int_or_none(video_data.get('broadcastDate') or video_data.get('startDate')),
            'formats': formats,
            'channel': video_data.get('channelName'),
            'channel_id': video_data.get('channelId'),
            'series': video_data.get('showName'),
            'season': video_data.get('seasonName'),
            'season_number': int_or_none(video_data.get('seasonNo')),
            'season_id': video_data.get('seasonId'),
            'episode': title,
            'episode_number': int_or_none(video_data.get('episodeNo')),
        }


class HotStarPlaylistIE(HotStarBaseIE):
    IE_NAME = 'hotstar:playlist'
    _VALID_URL = r'https?://(?:www\.)?hotstar\.com/tv/[^/]+/s-\w+/list/[^/]+/t-(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://www.hotstar.com/tv/savdhaan-india/s-26/list/popular-clips/t-3_2_26',
        'info_dict': {
            'id': '3_2_26',
        },
        'playlist_mincount': 20,
    }, {
        'url': 'https://www.hotstar.com/tv/savdhaan-india/s-26/list/extras/t-2480',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        collection = self._call_api('o/v1/tray/find', playlist_id, 'uqId')

        entries = [
            self.url_result(
                'https://www.hotstar.com/%s' % video['contentId'],
                ie=HotStarIE.ie_key(), video_id=video['contentId'])
            for video in collection['assets']['items']
            if video.get('contentId')]

        return self.playlist_result(entries, playlist_id)
