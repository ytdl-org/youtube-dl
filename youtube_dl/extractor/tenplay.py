# coding: utf-8
from __future__ import unicode_literals

from base64 import b64encode
from datetime import datetime
from json import dumps

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    parse_age_limit,
    parse_iso8601,
    # smuggle_url,
    try_get,
)


class TenPlayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?10play\.com\.au/(?:[^/]+/)+(?P<id>tpv\d{6}[a-z]{5})'
    _TESTS = [{
        'url': 'https://10play.com.au/neighbours/web-extras/season-39/nathan-borg-is-the-first-aussie-actor-with-a-cochlear-implant-to-join-neighbours/tpv210128qupwd',
        'info_dict': {
            'id': '6226844312001',
            'ext': 'mp4',
            'title': 'Nathan Borg Is The First Aussie Actor With A Cochlear Implant To Join Neighbours',
            'description': 'md5:a02d0199c901c2dd4c796f1e7dd0de43',
            'age_limit': 10,
            'timestamp': 1611810000,
            'upload_date': '20210128',
            'uploader_id': '2199827728001',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Only available in Australia',
    }, {
        'url': 'https://10play.com.au/masterchef/episodes/season-1/masterchef-s1-ep-1/tpv190718kwzga',
        'info_dict': {
            'id': '6060533435001',
            'ext': 'mp4',
            'title': 'MasterChef - S1 Ep. 1',
            'description': 'md5:4fe7b78e28af8f2d900cd20d900ef95c',
            'age_limit': 10,
            'timestamp': 1240828200,
            'upload_date': '20090427',
            'uploader_id': '2199827728001',
        },
        'params': {
            # 'format': 'bestvideo',
            'skip_download': True,
        },
        'skip': 'Requires email and password',
    }, {
        'url': 'https://10play.com.au/how-to-stay-married/web-extras/season-1/terrys-talks-ep-1-embracing-change/tpv190915ylupc',
        'only_matching': True,
    }]
    # BRIGHTCOVE_URL_TEMPLATE = 'https://players.brightcove.net/2199827728001/cN6vRtRQt_default/index.html?videoId=%s'
    _GEO_BYPASS = False
    _NETRC_MACHINE = 'tenplay'

    def _login(self):
        username, password = self._get_login_info()
        if not username or not password:
            raise ExtractorError('No login info available, needed for using %s.' % self.IE_NAME, expected=True)

        login_json = dumps({'email': username, 'password': password}, separators=(',', ':'))
        date = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        login_result = self._download_json(
            'https://10play.com.au/api/user/auth', None,
            note='Logging in',
            errnote='Login failed',
            headers={'X-Network-Ten-Auth': b64encode(date.encode('ascii'))},
            data=login_json.encode('utf-8'))

        self._session_token = try_get(
            login_result, lambda x: x['jwt']['accessToken'],
            compat_str)

    def _real_extract(self, url):
        content_id = self._match_id(url)
        video_api = 'https://10play.com.au/api/v1/videos/' + content_id

        data = self._download_json(
            'https://10play.com.au/api/video/' + content_id, content_id)
        video = data.get('video') or {}
        metadata = data.get('metaData') or {}
        headers = {}

        if video.get('memberGated') is True:
            self._login()
            headers = {'authorization': 'Bearer ' + self._session_token}

        video_data = self._download_json(video_api, content_id)
        brightcove_id = video_data.get('altId')
        playback_data = self._download_json(
            video_data.get('playbackApiEndpoint'), brightcove_id,
            headers=headers)

        # brightcove_url = smuggle_url(
        #     self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id,
        #     {'geo_countries': ['AU']})
        m3u8_url = self._request_webpage(playback_data.get('source'), brightcove_id).geturl()
        if '10play-not-in-oz' in m3u8_url:
            self.raise_geo_restricted(countries=['AU'])
        formats = self._extract_m3u8_formats(m3u8_url, brightcove_id, 'mp4')
        self._sort_formats(formats)

        return {
            # '_type': 'url_transparent',
            # 'url': brightcove_url,
            'formats': formats,
            'id': brightcove_id,
            'title': video.get('title') or metadata.get('pageContentName') or metadata['showContentName'],
            'description': video.get('description'),
            'age_limit': parse_age_limit(video.get('showRatingClassification') or metadata.get('showProgramClassification')),
            'series': metadata.get('showName'),
            'season': metadata.get('showContentSeason'),
            'timestamp': parse_iso8601(metadata.get('contentPublishDate') or metadata.get('pageContentPublishDate')),
            'thumbnail': video.get('poster'),
            'uploader_id': '2199827728001',
            # 'ie_key': 'BrightcoveNew',
        }
