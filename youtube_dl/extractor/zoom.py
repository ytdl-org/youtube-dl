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
    _VALID_URL = r'(?P<base_url>https?://(?:[^.]+\.)?zoom.us/)rec(?:ording)?/(?:play)/(?P<id>[A-Za-z0-9_.-]+)'
    _TEST = {
        'url': 'https://us06web.zoom.us/rec/play/W1ctyErikzJ2CxtwlsTW3xNbiMHze6ZkU1adqeshzivi58DHEJ-7HX2Z8-nqK80a8d4CWHAhrSpsl9mG.OaL6JvfC1gAa1EvZ?canPlayFromShare=true&from=share_recording_detail&continueMode=true&componentName=rec-play&originRequestUrl=https%3A%2F%2Fus06web.zoom.us%2Frec%2Fshare%2F60THDorqjAyUm_IXKS88Z4KgfYRAER3wIG20jgrLqaSFBWJW14qBVBRkfHylpFrk.KXJxuNLN0sRBXyvf',
        'md5': '934d7d10e04df5252dcb157ef615a983',
        'info_dict': {
            'id': 'W1ctyErikzJ2CxtwlsTW3xNbiMHze6ZkU1adqeshzivi58DHEJ-7HX2Z8-nqK80a8d4CWHAhrSpsl9mG.OaL6JvfC1gAa1EvZ',
            'ext': 'mp4',
            'title': 'Chipathon Bi-Weekly Meeting- Shared screen with speaker view',
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
        try:
            video_page = self._parse_json(self._download_webpage(
                base_url + "nws/recording/1.0/play/info/" + data["fileId"], play_id),
                play_id, js_to_json)
        except Exception:
            video_page = self._parse_json(self._download_webpage(
                base_url + "nws/recording/1.0/play/share-info/" + data["fileId"], play_id),
                play_id, js_to_json)
        return {
            'id': play_id,
            'title': video_page["result"]["meet"]["topic"],
            'url': video_page["result"]['viewMp4Url'],
            'width': int_or_none(video_page["result"]["viewResolvtions"][0]),
            'height': int_or_none(video_page["result"]["viewResolvtions"][1]),
            'http_headers': {
                'Referer': base_url,
            },
            'filesize_approx': parse_filesize(video_page["result"]["recording"]["fileSizeInMB"]),
        }
