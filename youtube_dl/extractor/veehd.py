from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    get_element_by_id,
    clean_html,
)


class VeeHDIE(InfoExtractor):
    _VALID_URL = r'https?://veehd\.com/video/(?P<id>\d+)'

    _TEST = {
        'url': 'http://veehd.com/video/4686958',
        'file': '4686958.mp4',
        'info_dict': {
            'title': 'Time Lapse View from Space ( ISS)',
            'uploader_id': 'spotted',
            'description': 'md5:f0094c4cf3a72e22bc4e4239ef767ad7',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        # VeeHD seems to send garbage on the first request.
        # See https://github.com/rg3/youtube-dl/issues/2102
        self._download_webpage(url, video_id, 'Requesting webpage')
        webpage = self._download_webpage(url, video_id)
        player_path = self._search_regex(
            r'\$\("#playeriframe"\).attr\({src : "(.+?)"',
            webpage, 'player path')
        player_url = compat_urlparse.urljoin(url, player_path)

        self._download_webpage(player_url, video_id, 'Requesting player page')
        player_page = self._download_webpage(
            player_url, video_id, 'Downloading player page')
        config_json = self._search_regex(
            r'value=\'config=({.+?})\'', player_page, 'config json')
        config = json.loads(config_json)

        video_url = compat_urlparse.unquote(config['clip']['url'])
        title = clean_html(get_element_by_id('videoName', webpage).rpartition('|')[0])
        uploader_id = self._html_search_regex(r'<a href="/profile/\d+">(.+?)</a>',
            webpage, 'uploader')
        thumbnail = self._search_regex(r'<img id="veehdpreview" src="(.+?)"',
            webpage, 'thumbnail')
        description = self._html_search_regex(r'<td class="infodropdown".*?<div>(.*?)<ul',
            webpage, 'description', flags=re.DOTALL)

        return {
            '_type': 'video',
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'mp4',
            'uploader_id': uploader_id,
            'thumbnail': thumbnail,
            'description': description,
        }
