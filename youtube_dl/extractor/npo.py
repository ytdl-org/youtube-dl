from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
)


class NPOIE(InfoExtractor):
    IE_NAME = 'npo.nl'
    _VALID_URL = r'https?://www\.npo\.nl/[^/]+/[^/]+/(?P<id>[^/?]+)'

    _TEST = {
        'url': 'http://www.npo.nl/nieuwsuur/22-06-2014/VPWON_1220719',
        'md5': '4b3f9c429157ec4775f2c9cb7b911016',
        'info_dict': {
            'id': 'VPWON_1220719',
            'ext': 'mp4',
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
        token = self._search_regex(r'npoplayer.token = "(.+?)"', token_page, 'token')
        streams_info = self._download_json(
            'http://ida.omroep.nl/odi/?prid=%s&puboptions=h264_std&adaptive=yes&token=%s' % (video_id, token),
            video_id
        )

        stream_info = self._download_json(
            streams_info['streams'][0] + '&type=json',
            video_id,
            'Downloading stream info'
        )

        return {
            'id': video_id,
            'title': metadata['titel'],
            'ext': 'mp4',
            'url': stream_info['url'],
            'description': metadata['info'],
            'thumbnail': metadata['images'][-1]['url'],
            'upload_date': unified_strdate(metadata['gidsdatum']),
        }
