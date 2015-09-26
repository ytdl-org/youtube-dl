# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
)


class VGTVIE(InfoExtractor):
    IE_DESC = 'VGTV and BTTV'
    _VALID_URL = r'''(?x)
                    (?:
                        vgtv:|
                        http://(?:www\.)?
                    )
                    (?P<host>vgtv|bt)
                    (?:
                        :|
                        \.no/(?:tv/)?\#!/(?:video|live)/
                    )
                    (?P<id>[0-9]+)
                    '''
    _TESTS = [
        {
            # streamType: vod
            'url': 'http://www.vgtv.no/#!/video/84196/hevnen-er-soet-episode-10-abu',
            'md5': 'b8be7a234cebb840c0d512c78013e02f',
            'info_dict': {
                'id': '84196',
                'ext': 'mp4',
                'title': 'Hevnen er søt: Episode 10 - Abu',
                'description': 'md5:e25e4badb5f544b04341e14abdc72234',
                'thumbnail': 're:^https?://.*\.jpg',
                'duration': 648.000,
                'timestamp': 1404626400,
                'upload_date': '20140706',
                'view_count': int,
            },
        },
        {
            # streamType: wasLive
            'url': 'http://www.vgtv.no/#!/live/100764/opptak-vgtv-foelger-em-kvalifiseringen',
            'info_dict': {
                'id': '100764',
                'ext': 'flv',
                'title': 'OPPTAK: VGTV følger EM-kvalifiseringen',
                'description': 'md5:3772d9c0dc2dff92a886b60039a7d4d3',
                'thumbnail': 're:^https?://.*\.jpg',
                'duration': 9103.0,
                'timestamp': 1410113864,
                'upload_date': '20140907',
                'view_count': int,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            # streamType: live
            'url': 'http://www.vgtv.no/#!/live/113063/direkte-v75-fra-solvalla',
            'info_dict': {
                'id': '113063',
                'ext': 'flv',
                'title': 're:^DIREKTE: V75 fra Solvalla [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
                'description': 'md5:b3743425765355855f88e096acc93231',
                'thumbnail': 're:^https?://.*\.jpg',
                'duration': 0,
                'timestamp': 1432975582,
                'upload_date': '20150530',
                'view_count': int,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.bt.no/tv/#!/video/100250/norling-dette-er-forskjellen-paa-1-divisjon-og-eliteserien',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        host = mobj.group('host')

        HOST_WEBSITES = {
            'vgtv': 'vgtv',
            'bt': 'bttv',
        }

        data = self._download_json(
            'http://svp.vg.no/svp/api/v1/%s/assets/%s?appName=%s-website'
            % (host, video_id, HOST_WEBSITES[host]),
            video_id, 'Downloading media JSON')

        if data.get('status') == 'inactive':
            raise ExtractorError(
                'Video %s is no longer available' % video_id, expected=True)

        streams = data['streamUrls']
        stream_type = data.get('streamType')

        formats = []

        hls_url = streams.get('hls')
        if hls_url:
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', m3u8_id='hls'))

        hds_url = streams.get('hds')
        # wasLive hds are always 404
        if hds_url and stream_type != 'wasLive':
            formats.extend(self._extract_f4m_formats(
                hds_url + '?hdcore=3.2.0&plugin=aasp-3.2.0.77.18',
                video_id, f4m_id='hds'))

        mp4_url = streams.get('mp4')
        if mp4_url:
            _url = hls_url or hds_url
            MP4_URL_TEMPLATE = '%s/%%s.%s' % (mp4_url.rpartition('/')[0], mp4_url.rpartition('.')[-1])
            for mp4_format in _url.split(','):
                m = re.search('(?P<width>\d+)_(?P<height>\d+)_(?P<vbr>\d+)', mp4_format)
                if not m:
                    continue
                width = int(m.group('width'))
                height = int(m.group('height'))
                vbr = int(m.group('vbr'))
                formats.append({
                    'url': MP4_URL_TEMPLATE % mp4_format,
                    'format_id': 'mp4-%s' % vbr,
                    'width': width,
                    'height': height,
                    'vbr': vbr,
                    'preference': 1,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._live_title(data['title']),
            'description': data['description'],
            'thumbnail': data['images']['main'] + '?t[]=900x506q80',
            'timestamp': data['published'],
            'duration': float_or_none(data['duration'], 1000),
            'view_count': data['displays'],
            'formats': formats,
            'is_live': True if stream_type == 'live' else False,
        }


class BTArticleIE(InfoExtractor):
    IE_NAME = 'bt:article'
    IE_DESC = 'Bergens Tidende Articles'
    _VALID_URL = 'http://(?:www\.)?bt\.no/(?:[^/]+/)+(?P<id>[^/]+)-\d+\.html'
    _TEST = {
        'url': 'http://www.bt.no/nyheter/lokalt/Kjemper-for-internatet-1788214.html',
        'md5': 'd055e8ee918ef2844745fcfd1a4175fb',
        'info_dict': {
            'id': '23199',
            'ext': 'mp4',
            'title': 'Alrekstad internat',
            'description': 'md5:dc81a9056c874fedb62fc48a300dac58',
            'thumbnail': 're:^https?://.*\.jpg',
            'duration': 191,
            'timestamp': 1289991323,
            'upload_date': '20101117',
            'view_count': int,
        },
    }

    def _real_extract(self, url):
        webpage = self._download_webpage(url, self._match_id(url))
        video_id = self._search_regex(
            r'SVP\.Player\.load\(\s*(\d+)', webpage, 'video id')
        return self.url_result('vgtv:bt:%s' % video_id, 'VGTV')


class BTVestlendingenIE(InfoExtractor):
    IE_NAME = 'bt:vestlendingen'
    IE_DESC = 'Bergens Tidende - Vestlendingen'
    _VALID_URL = 'http://(?:www\.)?bt\.no/spesial/vestlendingen/#!/(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.bt.no/spesial/vestlendingen/#!/86588',
        'md5': 'd7d17e3337dc80de6d3a540aefbe441b',
        'info_dict': {
            'id': '86588',
            'ext': 'mov',
            'title': 'Otto Wollertsen',
            'description': 'Vestlendingen Otto Fredrik Wollertsen',
            'timestamp': 1430473209,
            'upload_date': '20150501',
        },
    }

    def _real_extract(self, url):
        return self.url_result('xstream:btno:%s' % self._match_id(url), 'Xstream')
