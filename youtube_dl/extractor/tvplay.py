# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    parse_iso8601,
    qualities,
)


class TVPlayIE(InfoExtractor):
    IE_DESC = 'TV3Play and related services'
    _VALID_URL = r'''(?x)http://(?:www\.)?
        (?:tvplay\.lv/parraides|
           tv3play\.lt/programos|
           play\.tv3\.lt/programos|
           tv3play\.ee/sisu|
           tv3play\.se/program|
           tv6play\.se/program|
           tv8play\.se/program|
           tv10play\.se/program|
           tv3play\.no/programmer|
           viasat4play\.no/programmer|
           tv6play\.no/programmer|
           tv3play\.dk/programmer|
           play\.novatv\.bg/programi
        )/[^/]+/(?P<id>\d+)
        '''
    _TESTS = [
        {
            'url': 'http://www.tvplay.lv/parraides/vinas-melo-labak/418113?autostart=true',
            'info_dict': {
                'id': '418113',
                'ext': 'flv',
                'title': 'Kādi ir īri? - Viņas melo labāk',
                'description': 'Baiba apsmej īrus, kādi tie ir un ko viņi dara.',
                'duration': 25,
                'timestamp': 1406097056,
                'upload_date': '20140723',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://play.tv3.lt/programos/moterys-meluoja-geriau/409229?autostart=true',
            'info_dict': {
                'id': '409229',
                'ext': 'flv',
                'title': 'Moterys meluoja geriau',
                'description': 'md5:9aec0fc68e2cbc992d2a140bd41fa89e',
                'duration': 1330,
                'timestamp': 1403769181,
                'upload_date': '20140626',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.tv3play.ee/sisu/kodu-keset-linna/238551?autostart=true',
            'info_dict': {
                'id': '238551',
                'ext': 'flv',
                'title': 'Kodu keset linna 398537',
                'description': 'md5:7df175e3c94db9e47c0d81ffa5d68701',
                'duration': 1257,
                'timestamp': 1292449761,
                'upload_date': '20101215',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.tv3play.se/program/husraddarna/395385?autostart=true',
            'info_dict': {
                'id': '395385',
                'ext': 'flv',
                'title': 'Husräddarna S02E07',
                'description': 'md5:f210c6c89f42d4fc39faa551be813777',
                'duration': 2574,
                'timestamp': 1400596321,
                'upload_date': '20140520',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.tv6play.se/program/den-sista-dokusapan/266636?autostart=true',
            'info_dict': {
                'id': '266636',
                'ext': 'flv',
                'title': 'Den sista dokusåpan S01E08',
                'description': 'md5:295be39c872520221b933830f660b110',
                'duration': 1492,
                'timestamp': 1330522854,
                'upload_date': '20120229',
                'age_limit': 18,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.tv8play.se/program/antikjakten/282756?autostart=true',
            'info_dict': {
                'id': '282756',
                'ext': 'flv',
                'title': 'Antikjakten S01E10',
                'description': 'md5:1b201169beabd97e20c5ad0ad67b13b8',
                'duration': 2646,
                'timestamp': 1348575868,
                'upload_date': '20120925',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.tv3play.no/programmer/anna-anka-soker-assistent/230898?autostart=true',
            'info_dict': {
                'id': '230898',
                'ext': 'flv',
                'title': 'Anna Anka søker assistent - Ep. 8',
                'description': 'md5:f80916bf5bbe1c5f760d127f8dd71474',
                'duration': 2656,
                'timestamp': 1277720005,
                'upload_date': '20100628',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.viasat4play.no/programmer/budbringerne/21873?autostart=true',
            'info_dict': {
                'id': '21873',
                'ext': 'flv',
                'title': 'Budbringerne program 10',
                'description': 'md5:4db78dc4ec8a85bb04fd322a3ee5092d',
                'duration': 1297,
                'timestamp': 1254205102,
                'upload_date': '20090929',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.tv6play.no/programmer/hotelinspektor-alex-polizzi/361883?autostart=true',
            'info_dict': {
                'id': '361883',
                'ext': 'flv',
                'title': 'Hotelinspektør Alex Polizzi - Ep. 10',
                'description': 'md5:3ecf808db9ec96c862c8ecb3a7fdaf81',
                'duration': 2594,
                'timestamp': 1393236292,
                'upload_date': '20140224',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://play.novatv.bg/programi/zdravei-bulgariya/624952?autostart=true',
            'info_dict': {
                'id': '624952',
                'ext': 'flv',
                'title': 'Здравей, България (12.06.2015 г.) ',
                'description': 'md5:99f3700451ac5bb71a260268b8daefd7',
                'duration': 8838,
                'timestamp': 1434100372,
                'upload_date': '20150612',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            'http://playapi.mtgx.tv/v1/videos/%s' % video_id, video_id, 'Downloading video JSON')

        if video['is_geo_blocked']:
            self.report_warning(
                'This content might not be available in your country due to copyright reasons')

        streams = self._download_json(
            'http://playapi.mtgx.tv/v1/videos/stream/%s' % video_id, video_id, 'Downloading streams JSON')

        quality = qualities(['hls', 'medium', 'high'])
        formats = []
        for format_id, video_url in streams['streams'].items():
            if not video_url or not isinstance(video_url, compat_str):
                continue
            fmt = {
                'format_id': format_id,
                'preference': quality(format_id),
            }
            if video_url.startswith('rtmp'):
                m = re.search(r'^(?P<url>rtmp://[^/]+/(?P<app>[^/]+))/(?P<playpath>.+)$', video_url)
                if not m:
                    continue
                fmt.update({
                    'ext': 'flv',
                    'url': m.group('url'),
                    'app': m.group('app'),
                    'play_path': m.group('playpath'),
                })
            elif video_url.endswith('.f4m'):
                formats.extend(self._extract_f4m_formats(
                    video_url + '?hdcore=3.5.0&plugin=aasp-3.5.0.151.81', video_id))
                continue
            else:
                fmt.update({
                    'url': video_url,
                })
            formats.append(fmt)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video['title'],
            'description': video['description'],
            'duration': video['duration'],
            'timestamp': parse_iso8601(video['created_at']),
            'view_count': video['views']['total'],
            'age_limit': video.get('age_limit', 0),
            'formats': formats,
        }
