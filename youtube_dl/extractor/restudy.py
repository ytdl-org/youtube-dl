# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class RestudyIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?restudy\.dk/video/play/id/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.restudy.dk/video/play/id/1637',
        'info_dict': {
            'id': '1637',
            'ext': 'flv',
            'title': 'Leiden-frosteffekt',
            'description': 'Denne video er et eksperiment med flydende kvælstof.',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage).strip()
        description = self._og_search_description(webpage).strip()

        formats = self._extract_smil_formats(
            'https://www.restudy.dk/awsmedia/SmilDirectory/video_%s.xml' % video_id,
            video_id)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
        }
