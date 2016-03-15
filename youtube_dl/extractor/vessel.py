# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_iso8601,
    sanitized_Request,
)


class VesselIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vessel\.com/videos/(?P<id>[0-9a-zA-Z]+)'
    _API_URL_TEMPLATE = 'https://www.vessel.com/api/view/items/%s'
    _LOGIN_URL = 'https://www.vessel.com/api/account/login'
    _NETRC_MACHINE = 'vessel'
    _TEST = {
        'url': 'https://www.vessel.com/videos/HDN7G5UMs',
        'md5': '455cdf8beb71c6dd797fd2f3818d05c4',
        'info_dict': {
            'id': 'HDN7G5UMs',
            'ext': 'mp4',
            'title': 'Nvidia GeForce GTX Titan X - The Best Video Card on the Market?',
            'thumbnail': 're:^https?://.*\.jpg$',
            'upload_date': '20150317',
            'description': 'Did Nvidia pull out all the stops on the Titan X, or does its performance leave something to be desired?',
            'timestamp': int,
        },
    }

    @staticmethod
    def make_json_request(url, data):
        payload = json.dumps(data).encode('utf-8')
        req = sanitized_Request(url, payload)
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        return req

    @staticmethod
    def find_assets(data, asset_type, asset_id=None):
        for asset in data.get('assets', []):
            if not asset.get('type') == asset_type:
                continue
            elif asset_id is not None and not asset.get('id') == asset_id:
                continue
            else:
                yield asset

    def _check_access_rights(self, data):
        access_info = data.get('__view', {})
        if not access_info.get('allow_access', True):
            err_code = access_info.get('error_code') or ''
            if err_code == 'ITEM_PAID_ONLY':
                raise ExtractorError(
                    'This video requires subscription.', expected=True)
            else:
                raise ExtractorError(
                    'Access to this content is restricted. (%s said: %s)' % (self.IE_NAME, err_code), expected=True)

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return
        self.report_login()
        data = {
            'client_id': 'web',
            'type': 'password',
            'user_key': username,
            'password': password,
        }
        login_request = VesselIE.make_json_request(self._LOGIN_URL, data)
        self._download_webpage(login_request, None, False, 'Wrong login info')

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        data = self._parse_json(self._search_regex(
            r'App\.bootstrapData\((.*?)\);', webpage, 'data'), video_id)
        asset_id = data['model']['data']['id']

        req = VesselIE.make_json_request(
            self._API_URL_TEMPLATE % asset_id, {'client': 'web'})
        data = self._download_json(req, video_id)
        video_asset_id = data.get('main_video_asset')

        self._check_access_rights(data)

        try:
            video_asset = next(
                VesselIE.find_assets(data, 'video', asset_id=video_asset_id))
        except StopIteration:
            raise ExtractorError('No video assets found')

        formats = []
        for f in video_asset.get('sources', []):
            if f['name'] == 'hls-index':
                formats.extend(self._extract_m3u8_formats(
                    f['location'], video_id, ext='mp4', m3u8_id='m3u8'))
            else:
                formats.append({
                    'format_id': f['name'],
                    'tbr': f.get('bitrate'),
                    'height': f.get('height'),
                    'width': f.get('width'),
                    'url': f['location'],
                })
        self._sort_formats(formats)

        thumbnails = []
        for im_asset in VesselIE.find_assets(data, 'image'):
            thumbnails.append({
                'url': im_asset['location'],
                'width': im_asset.get('width', 0),
                'height': im_asset.get('height', 0),
            })

        return {
            'id': video_id,
            'title': data['title'],
            'formats': formats,
            'thumbnails': thumbnails,
            'description': data.get('short_description'),
            'duration': data.get('duration'),
            'comment_count': data.get('comment_count'),
            'like_count': data.get('like_count'),
            'view_count': data.get('view_count'),
            'timestamp': parse_iso8601(data.get('released_at')),
        }
