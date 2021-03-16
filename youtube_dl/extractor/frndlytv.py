# coding: utf-8
from __future__ import unicode_literals

import json
import uuid
from ..utils import ExtractorError
from .common import InfoExtractor


class FrndlyTVIE(InfoExtractor):
    _VALID_URL = r'https?://watch\.frndlytv\.com/epg/play/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://watch.frndlytv.com/epg/play/276975',
        'md5': '2be07362bfc04fd0ae5a7ba29612f3d2',
        'info_dict': {
            'id': '276975',
            'ext': 'mp4',
            'title': 'When Calls the Heart - Hallmark Channel - New | S8, Ep1 | Open Season | TVG | Sun, Feb 21 | 8:00 PM - 9:00 PM',
            'description': 'md5:30fd6a6da709fd0e2e48d4d9bf823f57'
        },
        'skip': 'Requires frndlytv account credentials',
    }
    _SITE_INFO_URL = 'https://watch.frndlytv.com/frndlytv.json'
    _NETRC_MACHINE = 'frndlytv'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Video details

        content_info = self._download_json(
            self._api_url + '/service/api/v1/page/content', video_id,
            query={
                'path': 'epg/play/%s' % video_id,
                'count': 1,
            },
            headers={
                'Accept': 'application/json, text/plain',
                'Content-Type': 'application/json',
                'box-id': self._box_id,
                'session-id': self._session_info['response']['sessionId'],
                'tenant-code': self._session_info['response']['tenantCode'],
            },
            note='Downloading info',
            errnote='Unable to download info')
        if not content_info['status']:
            raise ExtractorError('Unknown video', video_id=video_id)

        data_rows = next(pane['content']['dataRows']
                         for pane in content_info['response']['data'] if pane['paneType'] == 'content')
        data_rows_flat = [item for sublist in data_rows for item in sublist['elements']]

        title = next((item['data']
                     for item in data_rows_flat if item['elementType'] == 'text' and item['elementSubtype'] == 'title'),
                     None)

        subtitle = next((item['data']
                        for item in data_rows_flat if item['elementType'] == 'text' and item['elementSubtype'] == 'subtitle'),
                        None)

        subtitle_parts = []
        for i in range(1, 6):
            subtype = 'subtitle%d' % i
            subtitle_parts.append(
                next((item['data']
                     for item in data_rows_flat if item['elementType'] == 'text' and item['elementSubtype'] == subtype),
                     None))
        subtitle_extra = ''.join(filter(None, subtitle_parts))

        if subtitle:
            title += " - " + subtitle
        if subtitle_extra:
            title += " - " + subtitle_extra

        description = next((item['data'] for item in data_rows_flat if item['elementType'] == 'description'), None)

        # Stream details

        stream_info = self._download_json(
            self._api_url + '/service/api/v1/page/stream', video_id,
            query={
                'path': 'epg/play/%s' % video_id
            },
            headers={
                'Accept': 'application/json, text/plain',
                'box-id': self._box_id,
                'session-id': self._session_info['response']['sessionId'],
                'tenant-code': self._session_info['response']['tenantCode'],
            },
            note='Downloading stream info',
            errnote='Unable to download stream info')
        if not stream_info['status']:
            raise ExtractorError('Unknown video stream', video_id=video_id)

        formats = []
        for stream_info in stream_info['response']['streams']:
            stream_formats = self._extract_m3u8_formats(
                stream_info['url'], video_id, 'mp4')
            formats.extend(stream_formats)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
        }

    def _initialize_api(self):
        site_info = self._download_json(
            self._SITE_INFO_URL, None, note='Downloading site information',
            errnote='Unable to download site information')
        self._api_url = site_info['api']

        self._box_id = str(uuid.uuid4())

        self._session_info = self._download_json(
            self._api_url + '/service/api/v1/get/token', None,
            query={
                'tenant_code': site_info['tenantCode'],
                'product': site_info['product'],
                'box_id': self._box_id,
                'device_id': 5,
                'device_sub_type': 'Firefox,5,UNIX'
            },
            note='Starting site session',
            errnote='Unable to start fetch session')
        if not self._session_info['status']:
            raise ExtractorError('Unable to start site session')

    def _login(self):
        username, password = self._get_login_info()
        if username is None or password is None:
            self.raise_login_required()

        auth_data = {
            'login_id': username,
            'login_key': password,
            'manufacturer': '123',
            'login_mode': 1
        }
        login_response = self._download_json(
            self._api_url + '/service/api/auth/v1/signin', None,
            data=json.dumps(auth_data).encode('utf-8'),
            headers={
                'Accept': 'application/json, text/plain',
                'Content-Type': 'application/json',
                'box-id': self._box_id,
                'session-id': self._session_info['response']['sessionId'],
                'tenant-code': self._session_info['response']['tenantCode'],
            },
            note='Logging in',
            errnote='Unable to log in')
        if not login_response['status']:
            raise ExtractorError('Unable to log in')

    def _real_initialize(self):
        self._initialize_api()
        self._login()
