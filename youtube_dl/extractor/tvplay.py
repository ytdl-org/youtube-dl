# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urlparse,
)
from ..utils import (
    parse_iso8601,
    qualities,
    determine_ext,
    update_url_query,
    int_or_none,
)


class TVPlayIE(InfoExtractor):
    IE_DESC = 'TV3Play and related services'
    _VALID_URL = r'''(?x)https?://(?:www\.)?
        (?:tvplay(?:\.skaties)?\.lv/parraides|
           (?:tv3play|play\.tv3)\.lt/programos|
           tv3play(?:\.tv3)?\.ee/sisu|
           tv(?:3|6|8|10)play\.se/program|
           (?:(?:tv3play|viasat4play|tv6play)\.no|tv3play\.dk)/programmer|
           play\.novatv\.bg/programi
        )/[^/]+/(?P<id>\d+)
        '''
    _TESTS = [
        {
            'url': 'http://www.tvplay.lv/parraides/vinas-melo-labak/418113?autostart=true',
            'md5': 'a1612fe0849455423ad8718fe049be21',
            'info_dict': {
                'id': '418113',
                'ext': 'mp4',
                'title': 'Kādi ir īri? - Viņas melo labāk',
                'description': 'Baiba apsmej īrus, kādi tie ir un ko viņi dara.',
                'duration': 25,
                'timestamp': 1406097056,
                'upload_date': '20140723',
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
                'ext': 'mp4',
                'title': 'Husräddarna S02E07',
                'description': 'md5:f210c6c89f42d4fc39faa551be813777',
                'duration': 2574,
                'timestamp': 1400596321,
                'upload_date': '20140520',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.tv6play.se/program/den-sista-dokusapan/266636?autostart=true',
            'info_dict': {
                'id': '266636',
                'ext': 'mp4',
                'title': 'Den sista dokusåpan S01E08',
                'description': 'md5:295be39c872520221b933830f660b110',
                'duration': 1492,
                'timestamp': 1330522854,
                'upload_date': '20120229',
                'age_limit': 18,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.tv8play.se/program/antikjakten/282756?autostart=true',
            'info_dict': {
                'id': '282756',
                'ext': 'mp4',
                'title': 'Antikjakten S01E10',
                'description': 'md5:1b201169beabd97e20c5ad0ad67b13b8',
                'duration': 2646,
                'timestamp': 1348575868,
                'upload_date': '20120925',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.tv3play.no/programmer/anna-anka-soker-assistent/230898?autostart=true',
            'info_dict': {
                'id': '230898',
                'ext': 'mp4',
                'title': 'Anna Anka søker assistent - Ep. 8',
                'description': 'md5:f80916bf5bbe1c5f760d127f8dd71474',
                'duration': 2656,
                'timestamp': 1277720005,
                'upload_date': '20100628',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.viasat4play.no/programmer/budbringerne/21873?autostart=true',
            'info_dict': {
                'id': '21873',
                'ext': 'mp4',
                'title': 'Budbringerne program 10',
                'description': 'md5:4db78dc4ec8a85bb04fd322a3ee5092d',
                'duration': 1297,
                'timestamp': 1254205102,
                'upload_date': '20090929',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.tv6play.no/programmer/hotelinspektor-alex-polizzi/361883?autostart=true',
            'info_dict': {
                'id': '361883',
                'ext': 'mp4',
                'title': 'Hotelinspektør Alex Polizzi - Ep. 10',
                'description': 'md5:3ecf808db9ec96c862c8ecb3a7fdaf81',
                'duration': 2594,
                'timestamp': 1393236292,
                'upload_date': '20140224',
            },
            'params': {
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
        {
            'url': 'http://tvplay.skaties.lv/parraides/vinas-melo-labak/418113?autostart=true',
            'only_matching': True,
        },
        {
            'url': 'http://tv3play.tv3.ee/sisu/kodu-keset-linna/238551?autostart=true',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            'http://playapi.mtgx.tv/v1/videos/%s' % video_id, video_id, 'Downloading video JSON')

        title = video['title']

        if video.get('is_geo_blocked'):
            self.report_warning(
                'This content might not be available in your country due to copyright reasons')

        streams = self._download_json(
            'http://playapi.mtgx.tv/v1/videos/stream/%s' % video_id, video_id, 'Downloading streams JSON')

        quality = qualities(['hls', 'medium', 'high'])
        formats = []
        for format_id, video_url in streams.get('streams', {}).items():
            if not video_url or not isinstance(video_url, compat_str):
                continue
            ext = determine_ext(video_url)
            if ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    update_url_query(video_url, {
                        'hdcore': '3.5.0',
                        'plugin': 'aasp-3.5.0.151.81'
                    }), video_id, f4m_id='hds', fatal=False))
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            else:
                fmt = {
                    'format_id': format_id,
                    'quality': quality(format_id),
                    'ext': ext,
                }
                if video_url.startswith('rtmp'):
                    m = re.search(
                        r'^(?P<url>rtmp://[^/]+/(?P<app>[^/]+))/(?P<playpath>.+)$', video_url)
                    if not m:
                        continue
                    fmt.update({
                        'ext': 'flv',
                        'url': m.group('url'),
                        'app': m.group('app'),
                        'play_path': m.group('playpath'),
                    })
                else:
                    fmt.update({
                        'url': video_url,
                    })
                formats.append(fmt)
        self._sort_formats(formats)

        # TODO: webvtt in m3u8
        subtitles = {}
        sami_path = video.get('sami_path')
        if sami_path:
            lang = self._search_regex(
                r'_([a-z]{2})\.xml', sami_path, 'lang',
                default=compat_urlparse.urlparse(url).netloc.rsplit('.', 1)[-1])
            subtitles[lang] = [{
                'url': sami_path,
            }]

        return {
            'id': video_id,
            'title': title,
            'description': video.get('description'),
            'duration': int_or_none(video.get('duration')),
            'timestamp': parse_iso8601(video.get('created_at')),
            'view_count': int_or_none(video.get('views', {}).get('total')),
            'age_limit': int_or_none(video.get('age_limit', 0)),
            'formats': formats,
            'subtitles': subtitles,
        }
