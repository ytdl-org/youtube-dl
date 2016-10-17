from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    month_by_name,
    int_or_none,
)


class NDTVIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?ndtv\.com/video/player/[^/]*/[^/]*/(?P<id>[a-z0-9]+)'

    _TEST = {
        'url': 'http://www.ndtv.com/video/player/news/ndtv-exclusive-don-t-need-character-certificate-from-rahul-gandhi-says-arvind-kejriwal/300710',
        'md5': '39f992dbe5fb531c395d8bbedb1e5e88',
        'info_dict': {
            'id': '300710',
            'ext': 'mp4',
            'title': "NDTV exclusive: Don't need character certificate from Rahul Gandhi, says Arvind Kejriwal",
            'description': 'md5:ab2d4b4a6056c5cb4caa6d729deabf02',
            'upload_date': '20131208',
            'duration': 1327,
            'thumbnail': 'http://i.ndtvimg.com/video/images/vod/medium/2013-12/big_300710_1386518307.jpg',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        filename = self._search_regex(
            r"__filename='([^']+)'", webpage, 'video filename')
        video_url = ('http://bitcast-b.bitgravity.com/ndtvod/23372/ndtv/%s' %
                     filename)

        duration = int_or_none(self._search_regex(
            r"__duration='([^']+)'", webpage, 'duration', fatal=False))

        date_m = re.search(r'''(?x)
            <p\s+class="vod_dateline">\s*
                Published\s+On:\s*
                (?P<monthname>[A-Za-z]+)\s+(?P<day>[0-9]+),\s*(?P<year>[0-9]+)
            ''', webpage)
        upload_date = None

        if date_m is not None:
            month = month_by_name(date_m.group('monthname'))
            if month is not None:
                upload_date = '%s%02d%02d' % (
                    date_m.group('year'), month, int(date_m.group('day')))

        description = self._og_search_description(webpage)
        READ_MORE = ' (Read more)'
        if description.endswith(READ_MORE):
            description = description[:-len(READ_MORE)]

        title = self._og_search_title(webpage)
        TITLE_SUFFIX = ' - NDTV'
        if title.endswith(TITLE_SUFFIX):
            title = title[:-len(TITLE_SUFFIX)]

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': self._og_search_thumbnail(webpage),
            'duration': duration,
            'upload_date': upload_date,
        }
