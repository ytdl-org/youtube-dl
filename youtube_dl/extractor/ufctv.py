# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_duration,
    parse_iso8601,
    urlencode_postdata,
)


class UFCTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ufc\.tv/video/(?P<id>[^/]+)'
    _NETRC_MACHINE = 'ufctv'
    _TEST = {
        'url': 'https://www.ufc.tv/video/ufc-219-countdown-full-episode',
        'info_dict': {
            'id': '34167',
            'ext': 'mp4',
            'title': 'UFC 219 Countdown: Full Episode',
            'description': 'md5:26d4e8bf4665ae5878842d7050c3c646',
            'timestamp': 1513962360,
            'upload_date': '20171222',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }

    def _real_initialize(self):
        username, password = self._get_login_info()
        if username is None:
            return

        code = self._download_json(
            'https://www.ufc.tv/secure/authenticate',
            None, 'Logging in', data=urlencode_postdata({
                'username': username,
                'password': password,
                'format': 'json',
            })).get('code')
        if code and code != 'loginsuccess':
            raise ExtractorError(code, expected=True)

    def _real_extract(self, url):
        display_id = self._match_id(url)
        video_data = self._download_json(url, display_id, query={
            'format': 'json',
        })
        video_id = str(video_data['id'])
        title = video_data['name']
        m3u8_url = self._download_json(
            'https://www.ufc.tv/service/publishpoint', video_id, query={
                'type': 'video',
                'format': 'json',
                'id': video_id,
            }, headers={
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0_1 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A402 Safari/604.1',
            })['path']
        m3u8_url = m3u8_url.replace('_iphone.', '.')
        formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description'),
            'duration': parse_duration(video_data.get('runtime')),
            'timestamp': parse_iso8601(video_data.get('releaseDate')),
            'formats': formats,
        }
