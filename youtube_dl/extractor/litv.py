# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    smuggle_url,
    unsmuggle_url,
)


class LiTVIE(InfoExtractor):
    _VALID_URL = r'https?://www\.litv\.tv/vod/[^/]+/content\.do\?.*?\bid=(?P<id>[^&]+)'

    _URL_TEMPLATE = 'https://www.litv.tv/vod/%s/content.do?id=%s'

    _TESTS = [{
        'url': 'https://www.litv.tv/vod/drama/content.do?brc_id=root&id=VOD00041610&isUHEnabled=true&autoPlay=1',
        'info_dict': {
            'id': 'VOD00041606',
            'title': '花千骨',
        },
        'playlist_count': 50,
    }, {
        'url': 'https://www.litv.tv/vod/drama/content.do?brc_id=root&id=VOD00041610&isUHEnabled=true&autoPlay=1',
        'info_dict': {
            'id': 'VOD00041610',
            'ext': 'mp4',
            'title': '花千骨第1集',
            'thumbnail': 're:https?://.*\.jpg$',
            'description': 'md5:c7017aa144c87467c4fb2909c4b05d6f',
            'episode_number': 1,
        },
        'params': {
            'noplaylist': True,
            'skip_download': True,  # m3u8 download
        },
        'skip': 'Georestricted to Taiwan',
    }]

    def _extract_playlist(self, season_list, video_id, vod_data, view_data, prompt=True):
        episode_title = view_data['title']
        content_id = season_list['contentId']

        if prompt:
            self.to_screen('Downloading playlist %s - add --no-playlist to just download video %s' % (content_id, video_id))

        all_episodes = [
            self.url_result(smuggle_url(
                self._URL_TEMPLATE % (view_data['contentType'], episode['contentId']),
                {'force_noplaylist': True}))  # To prevent infinite recursion
            for episode in season_list['episode']]

        return self.playlist_result(all_episodes, content_id, episode_title)

    def _real_extract(self, url):
        url, data = unsmuggle_url(url, {})

        video_id = self._match_id(url)

        noplaylist = self._downloader.params.get('noplaylist')
        noplaylist_prompt = True
        if 'force_noplaylist' in data:
            noplaylist = data['force_noplaylist']
            noplaylist_prompt = False

        webpage = self._download_webpage(url, video_id)

        view_data = dict(map(lambda t: (t[0], t[2]), re.findall(
            r'viewData\.([a-zA-Z]+)\s*=\s*(["\'])([^"\']+)\2',
            webpage)))

        vod_data = self._parse_json(self._search_regex(
            'var\s+vod\s*=\s*([^;]+)', webpage, 'VOD data', default='{}'),
            video_id)

        season_list = list(vod_data.get('seasonList', {}).values())
        if season_list:
            if not noplaylist:
                return self._extract_playlist(
                    season_list[0], video_id, vod_data, view_data,
                    prompt=noplaylist_prompt)

            if noplaylist_prompt:
                self.to_screen('Downloading just video %s because of --no-playlist' % video_id)

        # In browsers `getMainUrl` request is always issued. Usually this
        # endpoint gives the same result as the data embedded in the webpage.
        # If georestricted, there are no embedded data, so an extra request is
        # necessary to get the error code
        video_data = self._parse_json(self._search_regex(
            r'uiHlsUrl\s*=\s*testBackendData\(([^;]+)\);',
            webpage, 'video data', default='{}'), video_id)
        if not video_data:
            payload = {
                'assetId': view_data['assetId'],
                'watchDevices': vod_data['watchDevices'],
                'contentType': view_data['contentType'],
            }
            video_data = self._download_json(
                'https://www.litv.tv/vod/getMainUrl', video_id,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'})

        if not video_data.get('fullpath'):
            error_msg = video_data.get('errorMessage')
            if error_msg == 'vod.error.outsideregionerror':
                self.raise_geo_restricted('This video is available in Taiwan only')
            if error_msg:
                raise ExtractorError('%s said: %s' % (self.IE_NAME, error_msg), expected=True)
            raise ExtractorError('Unexpected result from %s' % self.IE_NAME)

        formats = self._extract_m3u8_formats(
            video_data['fullpath'], video_id, ext='mp4', m3u8_id='hls')
        for a_format in formats:
            # LiTV HLS segments doesn't like compressions
            a_format.setdefault('http_headers', {})['Youtubedl-no-compression'] = True

        title = view_data['title'] + view_data.get('secondaryMark', '')
        description = view_data.get('description')
        thumbnail = view_data.get('imageFile')
        categories = [item['name'] for item in vod_data.get('category', [])]
        episode = int_or_none(view_data.get('episode'))

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'categories': categories,
            'episode_number': episode,
        }
