# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    unified_timestamp,
    clean_html,
    ExtractorError,
    try_get,
)


class LRTIE(InfoExtractor):
    IE_NAME = 'lrt.lt'
    _VALID_URL = r'https?://(?:www\.)?lrt\.lt(?P<path>/mediateka/irasas/(?P<id>[0-9]+))'
    _TESTS = [{
        # m3u8 download
        'url': 'https://www.lrt.lt/mediateka/irasas/2000078895/loterija-keno-loto',
        # md5 for first 10240 bytes of content
        'md5': '484f5f30e3382a1aa444debc9e6256ae',
        'info_dict': {
            'id': '2000078895',
            'ext': 'mp4',
            'title': 'Loterija \u201eKeno Loto\u201c',
            'description': 'Tira\u017eo nr.: 7993.',
            'timestamp': 1568658420,
            'tags': ['Loterija \u201eKeno Loto\u201c', 'LRT TELEVIZIJA'],
            'upload_date': '20190916',
        },
    }, {
        # m4a download
        'url': 'https://www.lrt.lt/mediateka/irasas/2000068931/vakaro-pasaka-bebriukas',
        # md5 for first 11297 bytes of content
        'md5': 'f02072fb3c416c1c8f5969ea7b70f53b',
        'info_dict': {
            'id': '2000068931',
            'ext': 'm4a',
            'title': 'Vakaro pasaka. Bebriukas',
            'description': 'Est\u0173 pasaka \u201eBebriukas\u201d. Skaito aktorius Antanas \u0160urna.',
            'timestamp': 1558461780,
            'tags': ['LRT RADIJAS', 'Vakaro pasaka', 'Bebriukas'],
            'upload_date': '20190521',
        },
    }]

    MEDIA_INFO_URL = 'https://www.lrt.lt/servisai/stream_url/vod/media_info/'
    THUMBNAIL_URL = 'https://www.lrt.lt'
    QUERY_URL = '/mediateka/irasas/'
    TIMEZONE = '+02:00'

    def _real_extract(self, url):
        id = self._match_id(url)
        media_info = self._download_json(self.MEDIA_INFO_URL, id, query={'url': self.QUERY_URL + id})
        playlist_item = try_get(media_info, lambda x: x['playlist_item'], dict)
        file = playlist_item['file']  # mandatory for lrt.lt extractor
        if not file:
            raise ExtractorError("Media info from server did not contain m3u8 file url")

        if ".m4a" in file:
            # audio only content
            formats = [{'url': file, 'vcodec': 'none', 'ext': 'm4a'}]
        else:
            formats = self._extract_m3u8_formats(file, id, 'mp4', entry_protocol='m3u8_native')

        # extracting timestamp variable for clarity
        timestamp = media_info.get('date', '').replace('.', '-') + self.TIMEZONE

        return {
            'id': id,
            'title': playlist_item.get('title') or id,
            'formats': formats,
            'thumbnail': self.THUMBNAIL_URL + playlist_item.get('image', '/images/default-img.svg'),
            'description': clean_html(try_get(media_info, lambda x: x['content'], compat_str)),
            'timestamp': unified_timestamp(timestamp) if timestamp != self.TIMEZONE else None,
            'tags': [i.get('name') for i in media_info.get('tags', [{}]) if i.get('name')],
        }

        return merge_dicts(clean_info, jw_data, json_ld_data)
