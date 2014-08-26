# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_request,
    parse_iso8601,
)


class SportDeutschlandIE(InfoExtractor):
    _VALID_URL = r'https?://sportdeutschland\.tv/(?P<sport>[^/?#]+)/(?P<id>[^?#/]+)(?:$|[?#])'
    _TEST = {
        'url': 'http://sportdeutschland.tv/badminton/live-li-ning-badminton-weltmeisterschaft-2014-kopenhagen',
        'info_dict': {
            'id': 'live-li-ning-badminton-weltmeisterschaft-2014-kopenhagen',
            'ext': 'mp4',
            'title': 'LIVE: Li-Ning Badminton Weltmeisterschaft 2014 Kopenhagen',
            'categories': ['Badminton'],
            'view_count': int,
            'thumbnail': 're:^https?://.*\.jpg',
            'description': 're:^Die Badminton-WM 2014 aus Kopenhagen LIVE',
            'timestamp': 1409043600,
            'upload_date': '20140826',
        },
        'params': {
            'skip_download': 'Live stream',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        sport_id = mobj.group('sport')

        api_url = 'http://splink.tv/api/permalinks/%s/%s' % (
            sport_id, video_id)
        req = compat_urllib_request.Request(api_url, headers={
            'Accept': 'application/vnd.vidibus.v2.html+json',
            'Referer': url,
        })
        data = self._download_json(req, video_id)

        categories = list(data.get('section', {}).get('tags', {}).values())
        asset = data['asset']

        smil_url = asset['video']
        m3u8_url = smil_url.replace('.smil', '.m3u8')
        formats = self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4')

        smil_doc = self._download_xml(
            smil_url, video_id, note='Downloading SMIL metadata')
        base_url = smil_doc.find('./head/meta').attrib['base']
        formats.extend([{
            'format_id': 'rmtp',
            'url': base_url,
            'play_path': n.attrib['src'],
            'ext': 'flv',
            'preference': -100,
            'format_note': 'Seems to fail at example stream',
        } for n in smil_doc.findall('./body/video')])
        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': asset['title'],
            'thumbnail': asset.get('image'),
            'description': asset.get('teaser'),
            'categories': categories,
            'view_count': asset.get('views'),
            'rtmp_live': asset['live'],
            'timestamp': parse_iso8601(asset.get('date')),
        }

