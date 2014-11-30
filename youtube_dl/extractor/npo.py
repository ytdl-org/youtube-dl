from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    parse_duration,
    qualities,
    strip_jsonp,
    url_basename,
)


class NPOIE(InfoExtractor):
    IE_NAME = 'npo.nl'
    _VALID_URL = r'https?://www\.npo\.nl/[^/]+/[^/]+/(?P<id>[^/?]+)'

    _TESTS = [
        {
            'url': 'http://www.npo.nl/nieuwsuur/22-06-2014/VPWON_1220719',
            'md5': '4b3f9c429157ec4775f2c9cb7b911016',
            'info_dict': {
                'id': 'VPWON_1220719',
                'ext': 'm4v',
                'title': 'Nieuwsuur',
                'description': 'Dagelijks tussen tien en elf: nieuws, sport en achtergronden.',
                'upload_date': '20140622',
            },
        },
        {
            'url': 'http://www.npo.nl/de-mega-mike-mega-thomas-show/27-02-2009/VARA_101191800',
            'md5': 'da50a5787dbfc1603c4ad80f31c5120b',
            'info_dict': {
                'id': 'VARA_101191800',
                'ext': 'm4v',
                'title': 'De Mega Mike & Mega Thomas show',
                'description': 'md5:3b74c97fc9d6901d5a665aac0e5400f4',
                'upload_date': '20090227',
                'duration': 2400,
            },
        },
        {
            'url': 'http://www.npo.nl/tegenlicht/25-02-2013/VPWON_1169289',
            'md5': 'f8065e4e5a7824068ed3c7e783178f2c',
            'info_dict': {
                'id': 'VPWON_1169289',
                'ext': 'm4v',
                'title': 'Tegenlicht',
                'description': 'md5:d6476bceb17a8c103c76c3b708f05dd1',
                'upload_date': '20130225',
                'duration': 3000,
            },
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        return self._get_info(video_id)

    def _get_info(self, video_id):
        metadata = self._download_json(
            'http://e.omroep.nl/metadata/aflevering/%s' % video_id,
            video_id,
            # We have to remove the javascript callback
            transform_source=strip_jsonp,
        )
        token_page = self._download_webpage(
            'http://ida.omroep.nl/npoplayer/i.js',
            video_id,
            note='Downloading token'
        )
        token = self._search_regex(r'npoplayer\.token = "(.+?)"', token_page, 'token')

        formats = []
        quality = qualities(['adaptive', 'wmv_sb', 'h264_sb', 'wmv_bb', 'h264_bb', 'wvc1_std', 'h264_std'])
        for format_id in metadata['pubopties']:
            format_info = self._download_json(
                'http://ida.omroep.nl/odi/?prid=%s&puboptions=%s&adaptive=yes&token=%s' % (video_id, format_id, token),
                video_id, 'Downloading %s JSON' % format_id)
            if format_info.get('error_code', 0) or format_info.get('errorcode', 0):
                continue
            streams = format_info.get('streams')
            if streams:
                video_info = self._download_json(
                    streams[0] + '&type=json',
                    video_id, 'Downloading %s stream JSON' % format_id)
            else:
                video_info = format_info
            video_url = video_info.get('url')
            if not video_url:
                continue
            if format_id == 'adaptive':
                formats.extend(self._extract_m3u8_formats(video_url, video_id))
            else:
                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                    'quality': quality(format_id),
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': metadata['titel'],
            'description': metadata['info'],
            'thumbnail': metadata.get('images', [{'url': None}])[-1]['url'],
            'upload_date': unified_strdate(metadata.get('gidsdatum')),
            'duration': parse_duration(metadata.get('tijdsduur')),
            'formats': formats,
        }


class TegenlichtVproIE(NPOIE):
    IE_NAME = 'tegenlicht.vpro.nl'
    _VALID_URL = r'https?://tegenlicht\.vpro\.nl/afleveringen/.*?'

    _TESTS = [
        {
            'url': 'http://tegenlicht.vpro.nl/afleveringen/2012-2013/de-toekomst-komt-uit-afrika.html',
            'md5': 'f8065e4e5a7824068ed3c7e783178f2c',
            'info_dict': {
                'id': 'VPWON_1169289',
                'ext': 'm4v',
                'title': 'Tegenlicht',
                'description': 'md5:d6476bceb17a8c103c76c3b708f05dd1',
                'upload_date': '20130225',
            },
        },
    ]

    def _real_extract(self, url):
        name = url_basename(url)
        webpage = self._download_webpage(url, name)
        urn = self._html_search_meta('mediaurn', webpage)
        info_page = self._download_json(
            'http://rs.vpro.nl/v2/api/media/%s.json' % urn, name)
        return self._get_info(info_page['mid'])
