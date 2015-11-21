# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    sanitized_Request,
)


class SportDeutschlandIE(InfoExtractor):
    _VALID_URL = r'https?://sportdeutschland\.tv/(?P<sport>[^/?#]+)/(?P<id>[^?#/]+)(?:$|[?#])'
    _TESTS = [{
        'url': 'http://sportdeutschland.tv/badminton/live-li-ning-badminton-weltmeisterschaft-2014-kopenhagen',
        'info_dict': {
            'id': 'live-li-ning-badminton-weltmeisterschaft-2014-kopenhagen',
            'ext': 'mp4',
            'title': 're:Li-Ning Badminton Weltmeisterschaft 2014 Kopenhagen',
            'categories': ['Badminton'],
            'view_count': int,
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 're:Die Badminton-WM 2014 aus Kopenhagen bei Sportdeutschland\.TV',
            'timestamp': int,
            'upload_date': 're:^201408[23][0-9]$',
        },
        'params': {
            'skip_download': 'Live stream',
        },
    }, {
        'url': 'http://sportdeutschland.tv/li-ning-badminton-wm-2014/lee-li-ning-badminton-weltmeisterschaft-2014-kopenhagen-herren-einzel-wei-vs',
        'info_dict': {
            'id': 'lee-li-ning-badminton-weltmeisterschaft-2014-kopenhagen-herren-einzel-wei-vs',
            'ext': 'mp4',
            'upload_date': '20140825',
            'description': 'md5:60a20536b57cee7d9a4ec005e8687504',
            'timestamp': 1408976060,
            'duration': 2732,
            'title': 'Li-Ning Badminton Weltmeisterschaft 2014 Kopenhagen: Herren Einzel, Wei Lee vs. Keun Lee',
            'thumbnail': 're:^https?://.*\.jpg$',
            'view_count': int,
            'categories': ['Li-Ning Badminton WM 2014'],

        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        sport_id = mobj.group('sport')

        api_url = 'http://proxy.vidibusdynamic.net/sportdeutschland.tv/api/permalinks/%s/%s?access_token=true' % (
            sport_id, video_id)
        req = sanitized_Request(api_url, headers={
            'Accept': 'application/vnd.vidibus.v2.html+json',
            'Referer': url,
        })
        data = self._download_json(req, video_id)

        asset = data['asset']
        categories = [data['section']['title']]

        formats = []
        smil_url = asset['video']
        if '.smil' in smil_url:
            m3u8_url = smil_url.replace('.smil', '.m3u8')
            formats.extend(
                self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4'))

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
        else:
            formats.append({'url': smil_url})

        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': asset['title'],
            'thumbnail': asset.get('image'),
            'description': asset.get('teaser'),
            'duration': asset.get('duration'),
            'categories': categories,
            'view_count': asset.get('views'),
            'rtmp_live': asset.get('live'),
            'timestamp': parse_iso8601(asset.get('date')),
        }
