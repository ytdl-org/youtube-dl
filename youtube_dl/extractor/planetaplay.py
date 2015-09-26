# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class PlanetaPlayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?planetaplay\.com/\?sng=(?P<id>[0-9]+)'
    _API_URL = 'http://planetaplay.com/action/playlist/?sng={0:}'
    _THUMBNAIL_URL = 'http://planetaplay.com/img/thumb/{thumb:}'
    _TEST = {
        'url': 'http://planetaplay.com/?sng=3586',
        'md5': '9d569dceb7251a4e01355d5aea60f9db',
        'info_dict': {
            'id': '3586',
            'ext': 'flv',
            'title': 'md5:e829428ee28b1deed00de90de49d1da1',
        },
        'skip': 'Not accessible from Travis CI server',
    }

    _SONG_FORMATS = {
        'lq': (0, 'http://www.planetaplay.com/videoplayback/{med_hash:}'),
        'hq': (1, 'http://www.planetaplay.com/videoplayback/hi/{med_hash:}'),
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        response = self._download_json(
            self._API_URL.format(video_id), video_id)['response']
        try:
            data = response.get('data')[0]
        except IndexError:
            raise ExtractorError(
                '%s: failed to get the playlist' % self.IE_NAME, expected=True)

        title = '{song_artists:} - {sng_name:}'.format(**data)
        thumbnail = self._THUMBNAIL_URL.format(**data)

        formats = []
        for format_id, (quality, url_template) in self._SONG_FORMATS.items():
            formats.append({
                'format_id': format_id,
                'url': url_template.format(**data),
                'quality': quality,
                'ext': 'flv',
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
        }
