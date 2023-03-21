# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_age_limit,
    unescapeHTML,
    str_to_int,
    urljoin
)

from datetime import datetime
import base64
import json


class TenPlayIE(InfoExtractor):
    _VALID_URL = r'''(?x)^
        https?://(?:www\.)?10play\.com\.au/(?:
            (?:[^/]+/)+(?P<id>tpv\d{6}[a-z]{5})| (?# Individual show id)
            (?P<show>[^/]+)/episodes/(?P<season>[^/]+)(?# Entire season playlist)
        )'''
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
            'skip_download': True,
            'usenetrc': True,
        }
    }, {
        'url': 'https://10play.com.au/how-to-stay-married/web-extras/season-1/terrys-talks-ep-1-embracing-change/tpv190915ylupc',
        'only_matching': True,
    }, {
        'info_dict': {
            'title': 'Season 2022'
        },
        'url': 'https://10play.com.au/the-bold-and-the-beautiful-fast-tracked/episodes/season-2022',
        'playlist_count': 256,
        'params': {
            'skip_download': True,
            'usenetrc': True,
        }
    }]

    _NETRC_MACHINE = '10play.com.au'
    _GEO_BYPASS = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._access_token = None

    def get_access_token(self, content_id):
        if self._access_token is None:
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

            self._access_token = token_data['jwt']['accessToken']

        return self._access_token

    def extract_playlist(self, url):
        matches = self._VALID_URL_RE.match(url)
        show = matches.group('show')
        season = matches.group('season')

        # The api/v1 endpoint is throwing up 403 Forbidden, so we need to use the old API
        season_info = self._download_json(
            f'https://10play.com.au/api/shows/{show}/episodes/{season}', f"{show}/{season}",
            note='Fetching playlist info')

        # Try to find a carousel with the title "episodes", otherwise default to the top one
        episodes_carousel = next((c for c in season_info['content'][0]['components'] if c['title'].lower() == 'episodes'),
                                 season_info['content'][0]['components'][0])

        episodes = episodes_carousel['slides']

        load_more_url = urljoin(url, episodes_carousel['loadMoreUrl'])

        while episodes_carousel['hasMore']:
            skip_ids = [ep['id'] for ep in episodes]

            episodes_carousel = self._download_json(
                load_more_url, f"{show}/{season}",
                note=f'Fetching episodes {len(skip_ids)}+',
                query={'skipIds[]': skip_ids})

            episodes += episodes_carousel['items']

        episodes_urls = [urljoin(url, ep['cardLink']) for ep in episodes]

        return self.playlist_from_matches(episodes_urls, playlist_title=season_info['content'][0].get('title'))

    # Altered version to check for geoblocking without extraneous HEAD request
    def _extract_m3u8_formats(self, m3u8_url, video_id, ext=None,
                              entry_protocol='m3u8', preference=None,
                              m3u8_id=None, note=None, errnote=None,
                              fatal=True, live=False, data=None, headers={},
                              query={}):
        res = self._download_webpage_handle(
            m3u8_url, video_id,
            note=note or 'Downloading m3u8 information',
            errnote=errnote or 'Failed to download m3u8 information',
            fatal=fatal, data=data, headers=headers, query=query)

        if res is False:
            return []

        m3u8_doc, urlh = res
        m3u8_url = urlh.geturl()

        if '10play-not-in-oz' in m3u8_url:
            self.raise_geo_restricted(countries=['AU'])

        return self._parse_m3u8_formats(
            m3u8_doc, m3u8_url, ext=ext, entry_protocol=entry_protocol,
            preference=preference, m3u8_id=m3u8_id, live=live)

    def _real_extract(self, url):
        content_id = self._match_id(url)

        if content_id is None or content_id == 'None':
            return self.extract_playlist(url)

        video_info = self._download_json(
            'https://10play.com.au/api/v1/videos/' + content_id, content_id, note='Fetching video info')

        playback_url = video_info['playbackApiEndpoint']

        headers = {}

        # Handle member-gated videos
        if video_info.get('memberGated'):
            access_token = self.get_access_token(content_id)
            headers.update(Authorization=f"Bearer {access_token}")

        playback_info = self._download_json(
            playback_url, content_id,
            note='Fetching playback info',
            headers=headers)

        formats = self._extract_m3u8_formats(playback_info['source'], content_id, 'mp4')
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
