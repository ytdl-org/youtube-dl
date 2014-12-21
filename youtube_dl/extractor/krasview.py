# encoding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unescapeHTML,
)


class KrasViewIE(InfoExtractor):
    IE_DESC = 'Красвью'
    _VALID_URL = r'https?://krasview\.ru/video/(?P<id>\d+)'

    _TEST = {
        'url': 'http://krasview.ru/video/512228',
        'md5': '3b91003cf85fc5db277870c8ebd98eae',
        'info_dict': {
            'id': '512228',
            'ext': 'mp4',
            'title': 'Снег, лёд, заносы',
            'description': 'Снято в городе Нягань, в Ханты-Мансийском автономном округе.',
            'duration': 27,
            'thumbnail': 're:^https?://.*\.jpg',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        flashvars = json.loads(self._search_regex(
            r'flashvars\s*:\s*({.+?})\s*}\);', webpage, 'flashvars'))

        video_url = flashvars['url']
        title = unescapeHTML(flashvars['title'])
        description = unescapeHTML(flashvars.get('subtitle') or self._og_search_description(webpage, default=None))
        thumbnail = flashvars['image']
        duration = int(flashvars['duration'])
        filesize = int(flashvars['size'])
        width = int_or_none(self._og_search_property('video:width', webpage, 'video width'))
        height = int_or_none(self._og_search_property('video:height', webpage, 'video height'))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'filesize': filesize,
            'width': width,
            'height': height,
        }
