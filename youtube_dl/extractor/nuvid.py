from __future__ import unicode_literals

import re

from .common import InfoExtractor


class NuvidIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www|m)\.nuvid\.com/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://m.nuvid.com/video/1310741/',
        'md5': 'eab207b7ac4fccfb4e23c86201f11277',
        'info_dict': {
            'id': '1310741',
            'ext': 'mp4',
            "title": "Horny babes show their awesome bodeis and",
            "age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        murl = url.replace('://www.', '://m.')
        webpage = self._download_webpage(murl, video_id)

        title = self._html_search_regex(
            r'<div class="title">\s+<h2[^>]*>([^<]+)</h2>',
            webpage, 'title').strip()

        url_end = self._html_search_regex(
            r'href="(/[^"]+)"[^>]*data-link_type="mp4"',
            webpage, 'video_url')
        video_url = 'http://m.nuvid.com' + url_end

        thumbnail = self._html_search_regex(
            r'href="(/thumbs/[^"]+)"[^>]*data-link_type="thumbs"',
            webpage, 'thumbnail URL', fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'thumbnail': thumbnail,
            'age_limit': 18,
        }
