# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    js_to_json,
    parse_filesize,
    urlencode_postdata,
)


class ZoomIE(InfoExtractor):
    IE_NAME = 'zoom'
    _VALID_URL = r'(?P<base_url>https?://(?:[^.]+\.)?zoom.us/)rec(?:ording)?/(?:play|share)/(?P<id>[A-Za-z0-9_.-]+)'
    _TEST = {
        'url': 'https://economist.zoom.us/rec/play/dUk_CNBETmZ5VA2BwEl-jjakPpJ3M1pcfVYAPRsoIbEByGsLjUZtaa4yCATQuOL3der8BlTwxQePl_j0.EImBkXzTIaPvdZO5',
        'md5': 'ab445e8c911fddc4f9adc842c2c5d434',
        'info_dict': {
            'id': 'dUk_CNBETmZ5VA2BwEl-jjakPpJ3M1pcfVYAPRsoIbEByGsLjUZtaa4yCATQuOL3der8BlTwxQePl_j0.EImBkXzTIaPvdZO5',
            'ext': 'mp4',
            'title': 'China\'s "two sessions" and the new five-year plan',
        }
    }

    def _real_extract(self, url):
        base_url, play_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, play_id)

        try:
            form = self._form_hidden_inputs('password_form', webpage)
        except ExtractorError:
            form = None
        if form:
            password = self._downloader.params.get('videopassword')
            if not password:
                raise ExtractorError(
                    'This video is protected by a passcode, use the --video-password option', expected=True)
            is_meeting = form.get('useWhichPasswd') == 'meeting'
            validation = self._download_json(
                base_url + 'rec/validate%s_passwd' % ('_meet' if is_meeting else ''),
                play_id, 'Validating passcode', 'Wrong passcode', data=urlencode_postdata({
                    'id': form[('meet' if is_meeting else 'file') + 'Id'],
                    'passwd': password,
                    'action': form.get('action'),
                }))
            if not validation.get('status'):
                raise ExtractorError(validation['errorMessage'], expected=True)
            webpage = self._download_webpage(url, play_id)

        data = self._parse_json(self._search_regex(
            r'(?s)window\.__data__\s*=\s*({.+?});',
            webpage, 'data'), play_id, js_to_json)

        return {
            'id': play_id,
            'title': data['topic'],
            'url': data['viewMp4Url'],
            'width': int_or_none(data.get('viewResolvtionsWidth')),
            'height': int_or_none(data.get('viewResolvtionsHeight')),
            'http_headers': {
                'Referer': base_url,
            },
            'filesize_approx': parse_filesize(data.get('fileSize')),
        }
