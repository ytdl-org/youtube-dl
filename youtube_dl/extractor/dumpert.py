# coding: utf-8
from __future__ import unicode_literals

import base64
import re

from .common import InfoExtractor
from ..compat import compat_urllib_request
from ..utils import qualities


class DumpertIE(InfoExtractor):
    _VALID_URL = r'(?P<protocol>https?)://(?:www\.)?dumpert\.nl/(?:mediabase|embed)/(?P<id>[0-9]+/[0-9a-zA-Z]+)'
    _TESTS = [{
        'url': 'http://www.dumpert.nl/mediabase/6646981/951bc60f/',
        'md5': '1b9318d7d5054e7dcb9dc7654f21d643',
        'info_dict': {
            'id': '6646981/951bc60f',
            'ext': 'mp4',
            'title': 'Ik heb nieuws voor je',
            'description': 'Niet schrikken hoor',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'http://www.dumpert.nl/embed/6675421/dc440fe7/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        protocol = mobj.group('protocol')

        url = '%s://www.dumpert.nl/mediabase/%s' % (protocol, video_id)
        req = compat_urllib_request.Request(url)
        req.add_header('Cookie', 'nsfw=1; cpc=10')
        webpage = self._download_webpage(req, video_id)

        files_base64 = self._search_regex(
            r'data-files="([^"]+)"', webpage, 'data files')

        files = self._parse_json(
            base64.b64decode(files_base64.encode('utf-8')).decode('utf-8'),
            video_id)

        quality = qualities(['flv', 'mobile', 'tablet', '720p'])

        formats = [{
            'url': video_url,
            'format_id': format_id,
            'quality': quality(format_id),
        } for format_id, video_url in files.items() if format_id != 'still']
        self._sort_formats(formats)

        title = self._html_search_meta(
            'title', webpage) or self._og_search_title(webpage)
        description = self._html_search_meta(
            'description', webpage) or self._og_search_description(webpage)
        thumbnail = files.get('still') or self._og_search_thumbnail(webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats
        }
