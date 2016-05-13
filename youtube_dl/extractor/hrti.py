# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError
)
from ..utils import (
    sanitized_Request,
    ExtractorError
)


class HRTiIE(InfoExtractor):
    '''
    Information Extractor for Croatian Radiotelevision video on demand site
    https://hrti.hrt.hr
    Reverse engineered from the JavaScript app in app.min.js
    '''
    _NETRC_MACHINE = 'hrti'

    APP_LANGUAGE = 'hr'
    APP_VERSION = '1.1'
    APP_PUBLICATION_ID = 'all_in_one'

    _VALID_URL = r'https?://hrti.hrt.hr/#/video/show/(?P<id>[0-9]+)/(?P<name>(\w|-)+)?'
    _TEST = {
        'url': 'https://hrti.hrt.hr/#/video/show/2181385/republika-dokumentarna-serija-16-hd',
        'info_dict': {
            'id': '2181385',
            'ext': 'mp4',
            'name': 'REPUBLIKA, dokumentarna serija (4_6)-2251938',
        },
        'skip': 'Requires login'
    }

    def _initialize_api(self):
        '''Initializes the API and obtains the required urls'''
        api_url = 'http://clientapi.hrt.hr/client_api.php/config/identify/format/json'
        app_data = json.dumps({
            'application_publication_id': HRTiIE.APP_PUBLICATION_ID
        })
        self.uuid = self._download_json(api_url, None, note='Getting UUID',
                                        errnote='Unable to obtain an UUID',
                                        data=app_data)['uuid']

        app_data = json.dumps({
            'uuid': self.uuid,
            'application_publication_id': HRTiIE.APP_PUBLICATION_ID,
            'screen_height': 1080,
            'screen_width': 1920,
            'os': 'Windows',
            'os_version': 'NT 4.0',
            'device_model_string_id': 'chrome 42.0.2311.135',
            'application_version': HRTiIE.APP_VERSION
        })

        req = sanitized_Request(api_url, data=app_data)
        req.get_method = lambda: 'PUT'

        resources = self._download_json(
            req, None, note='Getting API endpoint and session information',
            errnote='Unable to get endpoint and session information',
            headers={'Content-type': 'application/json'})

        self.session_id = resources['session_id']
        modules = resources['modules']

        self.search_url = modules['vod_catalog']['resources']['search']['uri']
        self.search_url = self.search_url.format(
            language=HRTiIE.APP_LANGUAGE,
            application_id=HRTiIE.APP_PUBLICATION_ID)

        self.login_url = modules['user']['resources']['login']['uri']
        self.login_url = self.login_url.format(session_id=self.session_id)
        self.login_url += '/format/json'

        self.logout_url = modules['user']['resources']['logout']['uri']

    def _login(self):
        '''Performs a login to the webservice'''
        (username, password) = self._get_login_info()

        if username is None or password is None:
            self.raise_login_required()

        auth_data = json.dumps({
            'username': username,
            'password': password,
        })
        try:
            auth_info = self._download_json(
                self.login_url, None, note='Authenticating',
                errnote='Unable to log in', data=auth_data)
        except ExtractorError as ee:
            if isinstance(ee.cause, compat_HTTPError) and ee.cause.code == 406:
                raise ExtractorError('Unable to login, ' +
                                     'incorrect username and/or password')
            raise

        self.token = auth_info['secure_streaming_token']
        self.access_token = auth_info['session_token']

        self.logout_url = self.logout_url.format(session_id=self.session_id,
                                                 access_token=self.access_token)
        self.logout_url += '/format/json'

    def _real_initialize(self):
        '''Performs necessary operations so that the information extractor is
        ready for operation'''
        self._initialize_api()
        self._login()

    def _logout(self):
        '''Performs logout from the webservice'''
        self._download_json(self.logout_url, None, note='Logout',
                            errnote='Unable to log out', fatal=False)

    def _real_extract(self, url):
        '''Extract the data necessary to download the video'''
        video_id = self._match_id(url)

        metadata_url = self.search_url + \
            '/video_id/{video_id}/format/json'.format(video_id=video_id)

        metadata = self._download_json(metadata_url, video_id,
                                       note='Getting video metadata')
        video = metadata['video'][0]
        title_info = video.get('title', {})
        title = title_info.get('title_long')
        description = title_info.get('summary_long')

        movie = video['video_assets']['movie'][0]
        url = movie['url'].format(TOKEN=self.token)

        formats = self._extract_m3u8_formats(url, video_id, 'mp4')

        self._sort_formats(formats)

        self._logout()

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
        }
