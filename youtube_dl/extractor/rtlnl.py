from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import parse_duration


class RtlXlIE(InfoExtractor):
    IE_NAME = 'rtlxl.nl'
    _VALID_URL = r'https?://www\.rtlxl\.nl/#!/[^/]+/(?P<uuid>[^/?]+)'

    _TEST = {
        'url': 'http://www.rtlxl.nl/#!/rtl-nieuws-132237/6e4203a6-0a5e-3596-8424-c599a59e0677',
        'md5': 'cc16baa36a6c169391f0764fa6b16654',
        'info_dict': {
            'id': '6e4203a6-0a5e-3596-8424-c599a59e0677',
            'ext': 'mp4',
            'title': 'RTL Nieuws - Laat',
            'description': 'md5:6b61f66510c8889923b11f2778c72dc5',
            'timestamp': 1408051800,
            'upload_date': '20140814',
            'duration': 576.880,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uuid = mobj.group('uuid')

        info = self._download_json(
            'http://www.rtl.nl/system/s4m/vfd/version=2/uuid=%s/fmt=flash/' % uuid,
            uuid)

        material = info['material'][0]
        episode_info = info['episodes'][0]

        progname = info['abstracts'][0]['name']
        subtitle = material['title'] or info['episodes'][0]['name']

        # Use unencrypted m3u8 streams (See https://github.com/rg3/youtube-dl/issues/4118)
        videopath = material['videopath'].replace('.f4m', '.m3u8')
        m3u8_url = 'http://manifest.us.rtl.nl' + videopath

        formats = self._extract_m3u8_formats(m3u8_url, uuid, ext='mp4')

        video_urlpart = videopath.split('/flash/')[1][:-5]
        PG_URL_TEMPLATE = 'http://pg.us.rtl.nl/rtlxl/network/%s/progressive/%s.mp4'

        formats.extend([
            {
                'url': PG_URL_TEMPLATE % ('a2m', video_urlpart),
                'format_id': 'pg-sd',
            },
            {
                'url': PG_URL_TEMPLATE % ('a3m', video_urlpart),
                'format_id': 'pg-hd',
                'quality': 0,
            }
        ])

        self._sort_formats(formats)

        return {
            'id': uuid,
            'title': '%s - %s' % (progname, subtitle),
            'formats': formats,
            'timestamp': material['original_date'],
            'description': episode_info['synopsis'],
            'duration': parse_duration(material.get('duration')),
        }
