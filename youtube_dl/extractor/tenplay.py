# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    HEADRequest,
    parse_age_limit,
    unescapeHTML,
    str_to_int,
)

from datetime import datetime
import base64
import json


class TenPlayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?10play\.com\.au/(?:[^/]+/)+(?P<id>tpv\d{6}[a-z]{5})'
    _TESTS = [{
        'url': 'https://10play.com.au/masterchef/episodes/season-1/episode-1/tpv220408msjpb',
        'info_dict': {
            'id': 'tpv220408msjpb',
            'ext': 'mp4',
            'title': 'MasterChef - S1 Ep. 1',
            'description': 'md5:4fe7b78e28af8f2d900cd20d900ef95c',
            'age_limit': 10,
            'timestamp': 1240828200,
            'upload_date': '20090427',
        },
        'params': {
            # 'format': 'bestvideo',
            'skip_download': True,
            'usenetrc': True,
        }
    }, {
        'url': 'https://10play.com.au/how-to-stay-married/web-extras/season-1/terrys-talks-ep-1-embracing-change/tpv190915ylupc',
        'only_matching': True,
    }]

    _NETRC_MACHINE = '10play.com.au'
    _GEO_BYPASS = False

    def get_access_token(self, content_id):
        # log in with username and password
        username, password = self._get_login_info()

        if username is None or password is None:
            self.raise_login_required()

        ten_auth_header = base64.b64encode(datetime.utcnow().strftime("%Y%m%d%H%M%S").encode())

        auth_request_data = json.dumps({"email": username, "password": password}).encode()
        token_data = self._download_json(
            'https://10play.com.au/api/user/auth', content_id,
            note='Logging in to 10play',
            data=auth_request_data,
            headers={
                'Content-Type': 'application/json;charset=utf-8',
                'X-Network-Ten-Auth': ten_auth_header
            })

        access_token = token_data['jwt']['accessToken']

        return {'Authorization': f"Bearer {access_token}"}

    def _real_extract(self, url):
        content_id = self._match_id(url)

        video_info = self._download_json(
            'https://10play.com.au/api/v1/videos/' + content_id, content_id, note='Fetching video info')

        playback_url = video_info['playbackApiEndpoint']

        headers = {}

        # Handle member-gated videos
        if video_info.get('memberGated'):
            extra_headers = self.get_access_token(content_id)
            headers.update(**extra_headers)

        playback_info = self._download_json(
            playback_url, content_id,
            note='Fetching playback info',
            headers=headers)

        m3u8_url = self._request_webpage(HEADRequest(playback_info['source']), content_id).geturl()
        if '10play-not-in-oz' in m3u8_url:
            self.raise_geo_restricted(countries=['AU'])

        formats = self._extract_m3u8_formats(m3u8_url, content_id, 'mp4')
        self._sort_formats(formats)

        return {
            'formats': formats,
            'id': content_id,
            'title': unescapeHTML(video_info.get('subtitle')) or unescapeHTML(video_info.get('title')),
            'description': unescapeHTML(video_info.get('description')),
            'age_limit': parse_age_limit(video_info.get('classification')),
            'series': video_info.get('tvShow'),
            'season': video_info.get('season'),
            'season_number': str_to_int(video_info.get('season')),
            'episode': unescapeHTML(video_info.get('title')),
            'episode_number': str_to_int(video_info.get('episode')),
            'timestamp': video_info.get('published'),
            'duration': video_info.get('duration'),
            'thumbnail': video_info.get('posterImageUrl'),
        }
