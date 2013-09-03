import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    get_element_by_id,
    clean_html,
)

class VeeHDIE(InfoExtractor):
    _VALID_URL = r'https?://veehd.com/video/(?P<id>\d+)'

    _TEST = {
        u'url': u'http://veehd.com/video/4686958',
        u'file': u'4686958.mp4',
        u'info_dict': {
            u'title': u'Time Lapse View from Space ( ISS)',
            u'uploader_id': u'spotted',
            u'description': u'md5:f0094c4cf3a72e22bc4e4239ef767ad7',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        player_path = self._search_regex(r'\$\("#playeriframe"\).attr\({src : "(.+?)"',
            webpage, u'player path')
        player_url = compat_urlparse.urljoin(url, player_path)
        player_page = self._download_webpage(player_url, video_id,
            u'Downloading player page')
        config_json = self._search_regex(r'value=\'config=({.+?})\'',
            player_page, u'config json')
        config = json.loads(config_json)

        video_url = compat_urlparse.unquote(config['clip']['url'])
        title = clean_html(get_element_by_id('videoName', webpage).rpartition('|')[0])
        uploader_id = self._html_search_regex(r'<a href="/profile/\d+">(.+?)</a>',
            webpage, u'uploader')
        thumbnail = self._search_regex(r'<img id="veehdpreview" src="(.+?)"',
            webpage, u'thumbnail')
        description = self._html_search_regex(r'<td class="infodropdown".*?<div>(.*?)<ul',
            webpage, u'description', flags=re.DOTALL)

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
