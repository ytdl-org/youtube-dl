from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
)


class UstudioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|v1)\.)?ustudio\.com/video/(?P<id>[^/]+)/(?P<display_id>[^/?#&]+)'
    _TEST = {
        'url': 'http://ustudio.com/video/Uxu2my9bgSph/san_francisco_golden_gate_bridge',
        'md5': '58bbfca62125378742df01fc2abbdef6',
        'info_dict': {
            'id': 'Uxu2my9bgSph',
            'display_id': 'san_francisco_golden_gate_bridge',
            'ext': 'mp4',
            'title': 'San Francisco: Golden Gate Bridge',
            'description': 'md5:23925500697f2c6d4830e387ba51a9be',
            'thumbnail': 're:^https?://.*\.jpg$',
            'upload_date': '20111107',
            'uploader': 'Tony Farley',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        config = self._download_xml(
            'http://v1.ustudio.com/embed/%s/ustudio/config.xml' % video_id,
            display_id)

        def extract(kind):
            return [{
                'url': item.attrib['url'],
                'width': int_or_none(item.get('width')),
                'height': int_or_none(item.get('height')),
            } for item in config.findall('./qualities/quality/%s' % kind) if item.get('url')]

        formats = extract('video')
        self._sort_formats(formats)

        webpage = self._download_webpage(url, display_id)

        title = self._og_search_title(webpage)
        upload_date = unified_strdate(self._search_regex(
            r'(?s)Uploaded by\s*.+?\s*on\s*<span>([^<]+)</span>',
            webpage, 'upload date', fatal=False))
        uploader = self._search_regex(
            r'Uploaded by\s*<a[^>]*>([^<]+)<',
            webpage, 'uploader', fatal=False)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnails': extract('image'),
            'upload_date': upload_date,
            'uploader': uploader,
            'formats': formats,
        }
