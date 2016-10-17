from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    clean_html,
    ExtractorError,
    determine_ext,
    sanitized_Request,
)


class XVideosIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?xvideos\.com/video(?P<id>[0-9]+)(?:.*)'
    _TEST = {
        'url': 'http://www.xvideos.com/video4588838/biker_takes_his_girl',
        'md5': '4b46ae6ea5e6e9086e714d883313c0c9',
        'info_dict': {
            'id': '4588838',
            'ext': 'flv',
            'title': 'Biker Takes his Girl',
            'age_limit': 18,
        }
    }

    _ANDROID_USER_AGENT = 'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        mobj = re.search(r'<h1 class="inlineError">(.+?)</h1>', webpage)
        if mobj:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, clean_html(mobj.group(1))), expected=True)

        video_url = compat_urllib_parse_unquote(
            self._search_regex(r'flv_url=(.+?)&', webpage, 'video URL'))
        video_title = self._html_search_regex(
            r'<title>(.*?)\s+-\s+XVID', webpage, 'title')
        video_thumbnail = self._search_regex(
            r'url_bigthumb=(.+?)&amp', webpage, 'thumbnail', fatal=False)

        formats = [{
            'url': video_url,
        }]

        android_req = sanitized_Request(url)
        android_req.add_header('User-Agent', self._ANDROID_USER_AGENT)
        android_webpage = self._download_webpage(android_req, video_id, fatal=False)

        if android_webpage is not None:
            player_params_str = self._search_regex(
                'mobileReplacePlayerDivTwoQual\(([^)]+)\)',
                android_webpage, 'player parameters', default='')
            player_params = list(map(lambda s: s.strip(' \''), player_params_str.split(',')))
            if player_params:
                formats.extend([{
                    'url': param,
                    'preference': -10,
                } for param in player_params if determine_ext(param) == 'mp4'])

        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': video_title,
            'ext': 'flv',
            'thumbnail': video_thumbnail,
            'age_limit': 18,
        }
