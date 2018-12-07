# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class RegioTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?regio-tv\.de/.*vidid,(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.regio-tv.de/video_video,-nikolaus-besucht-sindelfinger-markt-_vidid,151732.html',
        'info_dict': {
            'id': '151732',
            'ext': 'mp4',
            'title': 'Nikolaus besucht Sindelfinger Markt',
            'description': 'md5:205f8c1aa68fcc110c54a4e82b4ce43b',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        key = self._search_regex(
            r'key\s*=\s*(?P<key>[0-9a-f]+)', webpage, 'key', group='key')
        title = self._og_search_title(webpage)

        video_url = 'https://vimp.schwaebische.de/getMedia.php?key=%s&type=mp4' % key
        description = self._og_search_description(
            webpage) or self._html_search_meta('description', webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        if thumbnail and thumbnail.startswith('/'):
            thumbnail = 'https://regio-tv.de' + thumbnail

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }
