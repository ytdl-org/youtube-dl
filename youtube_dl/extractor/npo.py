from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    qualities,
)


class NPOIE(InfoExtractor):
    IE_NAME = 'npo.nl'
    _VALID_URL = r'https?://www\.npo\.nl/[^/]+/[^/]+/(?P<id>[^/?]+)'

    _TEST = {
        'url': 'http://www.npo.nl/nieuwsuur/22-06-2014/VPWON_1220719',
        'md5': '4b3f9c429157ec4775f2c9cb7b911016',
        'info_dict': {
            'id': 'VPWON_1220719',
            'ext': 'm4v',
            'title': 'Nieuwsuur',
            'description': 'Dagelijks tussen tien en elf: nieuws, sport en achtergronden.',
            'upload_date': '20140622',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        metadata = self._download_json(
            'http://e.omroep.nl/metadata/aflevering/%s' % video_id,
            video_id,
            # We have to remove the javascript callback
            transform_source=lambda j: re.sub(r'parseMetadata\((.*?)\);\n//.*$', r'\1', j)
        )
        token_page = self._download_webpage(
            'http://ida.omroep.nl/npoplayer/i.js',
            video_id,
            note='Downloading token'
        )
        token = self._search_regex(r'npoplayer\.token = "(.+?)"', token_page, 'token')

        formats = []
        quality = qualities(['adaptive', 'h264_sb', 'h264_bb', 'h264_std'])
        for format_id in metadata['pubopties']:
            streams_info = self._download_json(
                'http://ida.omroep.nl/odi/?prid=%s&puboptions=%s&adaptive=yes&token=%s' % (video_id, format_id, token),
                video_id, 'Downloading %s streams info' % format_id)
            stream_info = self._download_json(
                streams_info['streams'][0] + '&type=json',
                video_id, 'Downloading %s stream info' % format_id)
            if format_id == 'adaptive':
                formats.extend(self._extract_m3u8_formats(stream_info['url'], video_id))
            else:
                formats.append({
                    'url': stream_info['url'],
                    'format_id': format_id,
                    'quality': quality(format_id),
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': metadata['titel'],
            'description': metadata['info'],
            'thumbnail': metadata['images'][-1]['url'],
            'upload_date': unified_strdate(metadata['gidsdatum']),
            'formats': formats,
        }
