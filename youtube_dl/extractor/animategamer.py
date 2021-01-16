# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random

from .common import InfoExtractor
from ..utils import ExtractorError


class AnimateGamerIE(InfoExtractor):
    _VALID_URL = r'https://ani\.gamer\.com\.tw/animeVideo.php\?sn=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://ani.gamer.com.tw/animeVideo.php?sn=11441',
        'md5': '00d08c66bf9a998f8b13e4882277a002',
        'info_dict': {
            'id': '11441',
            'ext': 'ts',
            'title': '巴哈姆特之怒 -Manaria Friends-[1]',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        base_ajax_url = 'https://ani.gamer.com.tw/ajax/'
        get_device_id_url = base_ajax_url + 'getdeviceid.php?id='

        device_id = self._download_json(
            get_device_id_url,
            video_id,
            note='Getting device ID',
            errnote='Unable to get device ID',
        )['deviceid']

        # TODO: is it necessary to get ad_id and s?
        tokens = {
            'video_id': video_id,
            'device_id': device_id,
            'ad_id': 0,
            's': 0,
            'token_hash': ''.join([random.choice('0123456789abcdef') for _ in range(12)]),
        }

        get_token_url = \
            base_ajax_url \
            + 'token.php?adID={ad_id}&sn={video_id}&device={device_id}&hash={token_hash}'.format(**tokens)
        ad_url = \
            base_ajax_url \
            + 'videoCastcishu.php?s={s}&sn={video_id}'.format(**tokens)
        ad_end_url = \
            base_ajax_url \
            + 'videoCastcishu.php?s={s}&sn={video_id}&ad=end'.format(**tokens)
        master_playlist_loc_url = \
            base_ajax_url \
            + 'm3u8.php?sn={video_id}&device={device_id}'.format(**tokens)

        info = self._download_json(get_token_url, video_id, note='Getting Token', fatal=False)

        is_vip = info.get('vip')

        if not is_vip:
            self._request_webpage(ad_url, video_id, note='Getting ad')
            self._sleep(10, video_id)
            self._request_webpage(ad_end_url, video_id, note='Skipping ad')

        master_playlist_url = self._download_json(
            master_playlist_loc_url,
            video_id,
            note='Getting master playlist url',
            errnote='Unable to get master playlist url',
        )['src']

        if not master_playlist_url:
            raise ExtractorError(msg='Unable to get master playlist url')

        master_playlist = self._extract_m3u8_formats(
            master_playlist_url,
            video_id,
            ext='ts',
            headers={'origin': 'https://ani.gamer.com.tw'})

        for entry in master_playlist:
            entry['http_headers'] = {'origin': 'https://ani.gamer.com.tw'}

        return {
            'id': video_id,
            'title': self._og_search_title(webpage).replace("線上看", "").strip(),
            'formats': master_playlist,
        }
