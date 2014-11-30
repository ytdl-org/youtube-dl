from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    js_to_json,
    qualities,
    determine_ext,
)


class PornHdIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?pornhd\.com/(?:[a-z]{2,4}/)?videos/(?P<id>\d+)(?:/(?P<display_id>.+))?'
    _TEST = {
        'url': 'http://www.pornhd.com/videos/1962/sierra-day-gets-his-cum-all-over-herself-hd-porn-video',
        'md5': '956b8ca569f7f4d8ec563e2c41598441',
        'info_dict': {
            'id': '1962',
            'display_id': 'sierra-day-gets-his-cum-all-over-herself-hd-porn-video',
            'ext': 'mp4',
            'title': 'Sierra loves doing laundry',
            'description': 'md5:8ff0523848ac2b8f9b065ba781ccf294',
            'thumbnail': 're:^https?://.*\.jpg',
            'view_count': int,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id or video_id)

        title = self._html_search_regex(
            r'<title>(.+) porn HD.+?</title>', webpage, 'title')
        description = self._html_search_regex(
            r'<div class="description">([^<]+)</div>', webpage, 'description', fatal=False)
        view_count = int_or_none(self._html_search_regex(
            r'(\d+) views\s*</span>', webpage, 'view count', fatal=False))
        thumbnail = self._search_regex(
            r"'poster'\s*:\s*'([^']+)'", webpage, 'thumbnail', fatal=False)

        quality = qualities(['SD', 'HD'])
        formats = [{
            'url': source['file'],
            'format_id': '%s-%s' % (source['label'], determine_ext(source['file'])),
            'quality': quality(source['label']),
        } for source in json.loads(js_to_json(self._search_regex(
            r"(?s)'sources'\s*:\s*(\[.+?\])", webpage, 'sources')))]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'formats': formats,
            'age_limit': 18,
        }
