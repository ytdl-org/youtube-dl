# encoding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_str,
    unescapeHTML,
)


class VKIE(InfoExtractor):
    IE_NAME = 'vk.com'
    _VALID_URL = r'https?://vk\.com/(?:videos.*?\?.*?z=)?video(?P<id>.*?)(?:\?|%2F|$)'

    _TESTS = [{
        'url': 'http://vk.com/videos-77521?z=video-77521_162222515%2Fclub77521',
        'file': '162222515.flv',
        'md5': '0deae91935c54e00003c2a00646315f0',
        'info_dict': {
            'title': 'ProtivoGunz - Хуёвая песня',
            'uploader': 'Noize MC',
        },
    },
    {
        'url': 'http://vk.com/video4643923_163339118',
        'file': '163339118.mp4',
        'md5': 'f79bccb5cd182b1f43502ca5685b2b36',
        'info_dict': {
            'uploader': 'Elvira Dzhonik',
            'title': 'Dream Theater - Hollow Years Live at Budokan 720*',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        info_url = 'http://vk.com/al_video.php?act=show&al=1&video=%s' % video_id
        info_page = self._download_webpage(info_url, video_id)
        m_yt = re.search(r'src="(http://www.youtube.com/.*?)"', info_page)
        if m_yt is not None:
            self.to_screen(u'Youtube video detected')
            return self.url_result(m_yt.group(1), 'Youtube')
        data_json = self._search_regex(r'var vars = ({.*?});', info_page, 'vars')
        data = json.loads(data_json)

        formats = [{
            'format_id': k,
            'url': v,
            'width': int(k[len('url'):]),
        } for k, v in data.items()
            if k.startswith('url')]
        self._sort_formats(formats)

        return {
            'id': compat_str(data['vid']),
            'formats': formats,
            'title': unescapeHTML(data['md_title']),
            'thumbnail': data.get('jpg'),
            'uploader': data.get('md_author'),
        }
