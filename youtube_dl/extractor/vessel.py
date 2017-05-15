# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_iso8601,
    sanitized_Request,
)


class VesselIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vessel\.com/(?:videos|embed)/(?P<id>[0-9a-zA-Z-_]+)'
    _API_URL_TEMPLATE = 'https://www.vessel.com/api/view/items/%s'
    _LOGIN_URL = 'https://www.vessel.com/api/account/login'
    _NETRC_MACHINE = 'vessel'
    _TESTS = [{
        'url': 'https://www.vessel.com/videos/HDN7G5UMs',
        'md5': '455cdf8beb71c6dd797fd2f3818d05c4',
        'info_dict': {
            'id': 'HDN7G5UMs',
            'ext': 'mp4',
            'title': 'Nvidia GeForce GTX Titan X - The Best Video Card on the Market?',
            'thumbnail': r're:^https?://.*\.jpg$',
            'upload_date': '20150317',
            'description': 'Did Nvidia pull out all the stops on the Titan X, or does its performance leave something to be desired?',
            'timestamp': int,
        },
    }, {
        'url': 'https://www.vessel.com/embed/G4U7gUJ6a?w=615&h=346',
        'only_matching': True,
    }, {
        'url': 'https://www.vessel.com/videos/F01_dsLj1',
        'only_matching': True,
    }, {
        'url': 'https://www.vessel.com/videos/RRX-sir-J',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return [url for _, url in re.findall(
            r'<iframe[^>]+src=(["\'])((?:https?:)?//(?:www\.)?vessel\.com/embed/[0-9a-zA-Z-_]+.*?)\1',
            webpage)]

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
            location = f.get('location')
            if not location:
                continue
            name = f.get('name')
            if name == 'hls-index':
                formats.extend(self._extract_m3u8_formats(
                    location, video_id, ext='mp4',
                    entry_protocol='m3u8_native', m3u8_id='m3u8', fatal=False))
            elif name == 'dash-index':
                formats.extend(self._extract_mpd_formats(
                    location, video_id, mpd_id='dash', fatal=False))
            else:
                formats.append({
                    'format_id': name,
                    'tbr': f.get('bitrate'),
                    'height': f.get('height'),
                    'width': f.get('width'),
                    'url': location,
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
