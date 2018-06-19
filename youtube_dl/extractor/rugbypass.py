# coding: utf-8
from __future__ import unicode_literals

from uuid import uuid4
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    urlencode_postdata,
    parse_iso8601,
    int_or_none,
)
from ..compat import compat_urlparse


class RugbyPassIE(InfoExtractor):
    _VALID_URL = r'https?://watch\.rugbypass\.com/game/(?P<id>([a-z]+\-)+[0-9]+)'
    _NETRC_MACHINE = 'rugbypass'
    _GEO_COUNTRIES = ['BD', 'BT', 'BN', 'KH', 'CN', 'TL', 'HK', 'IN', 'ID', 'LA', 'MO', 'MY', 'MV', 'MM', 'NP', 'PK', 'PH', 'SG', 'KR', 'LK', 'TW', 'TH', 'VN']
    _TESTS = [
        {
            'url': 'https://watch.rugbypass.com/game/wales-at-argentina-on-06162018',
            'md5': '8de5de440436f826d5407c17a016e137',
            'info_dict': {
                'id': '4823',
                'ext': 'mp4',
                'title': 'Argentina vs Wales - Full Game',
                'upload_date': '20180616',
                'timestamp': 1529177393,
            },
            'skip': 'Requires account credentials',
        },
        {
            'url': 'https://watch.rugbypass.com/game/wales-at-argentina-on-06162018?type=condensed',
            'md5': '40b177481dce360ee965bfb6751e9fd9',
            'info_dict': {
                'id': '4823',
                'ext': 'mp4',
                'title': 'Argentina vs Wales - Condensed',
                'upload_date': '20180616',
                'timestamp': 1529177393,
            },
            'skip': 'Requires account credentials',
        }
    ]
    _GAME_STATES = {'UPCOMING': 0, 'LIVE': 1, 'PROCESSING': 2, 'PLAYED': 3}
    _STREAM_TYPES = {'FULL': 1, 'CONDENSED': 8}

    def _real_initialize(self):
        self._login()

    def _login(self):
        username, password = self._get_login_info()
        if username is None or password is None:
            self.raise_login_required()

        login_data = {
            'username': username,
            'password': password,
            'deviceid': uuid4().hex,
            'devicetype': 8,
            'format': 'json'
        }

        response = self._download_json(
            'https://watch.rugbypass.com/secure/authenticate',
            None,
            data=urlencode_postdata(login_data))

        if response is False or response.get('code') != 'loginsuccess':
            raise ExtractorError('Login to RugbyPass failed', expected=True)

    def _extract_stream_type(self, url):
        parsed_url = compat_urlparse.urlparse(url)
        query = compat_urlparse.parse_qs(parsed_url.query)
        if 'type' in query and query['type'] == ['condensed']:
            return self._STREAM_TYPES['CONDENSED'], 'Condensed'
        return self._STREAM_TYPES['FULL'], 'Full Game'

    def _download_game_info(self, video_id):
        response = self._download_json('https://watch.rugbypass.com/scoreboard?format=json', video_id)

        if response is False or len(response.get('games', [])) == 0:
            raise ExtractorError('Failed to fetch games info', expected=True)

        games = response['games']
        game = next((g for g in games if g['seoName'] == video_id), None)

        if game is None:
            msg = 'Game %s was not found' % (video_id)
            raise ExtractorError(msg, expected=True)

        if game['gameState'] == self._GAME_STATES['UPCOMING']:
            msg = 'Game %s has not yet been played. It will air at %s GMT' % (video_id, game['dateTimeGMT'])
            raise ExtractorError(msg, expected=True)

        return game

    def _gather_formats(self, video_id, game_info, stream_type):
        video_data = {
            'id': int_or_none(game_info['id']),
            'gs': game_info['gameState'],
            'gt': stream_type,
            'type': 'game',
            'format': 'json',
        }

        if game_info['gameState'] == self._GAME_STATES['PROCESSING']:
            # Restart the live stream
            start_ms = parse_iso8601(game_info['dateTimeGMT']) * 1000
            end_ms = parse_iso8601(game_info['endDateTimeGMT']) * 1000

            video_data['st'] = start_ms
            video_data['dur'] = end_ms - start_ms

        response = self._download_json(
            'https://watch.rugbypass.com/service/publishpoint',
            video_id,
            data=urlencode_postdata(video_data))

        if response is False or len(response.get('path', '')) == 0:
            msg = 'Failed to load stream for %s' % (video_id)
            raise ExtractorError(msg, expected=True)

        formats = self._extract_m3u8_formats(response['path'], video_id, ext='mp4')
        self._sort_formats(formats)

        return formats

    def _real_extract(self, url):
        video_id = self._match_id(url)
        stream_type, stream_type_description = self._extract_stream_type(url)

        game_info = self._download_game_info(video_id)

        title = game_info['homeTeam']['name'] + ' vs ' + game_info['awayTeam']['name'] + ' - ' + stream_type_description
        aired = parse_iso8601(game_info['dateTimeGMT'])

        formats = self._gather_formats(video_id, game_info, stream_type)

        return {
            'id': game_info['id'],
            'title': title,
            'timestamp': aired,
            'formats': formats,
        }
