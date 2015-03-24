from __future__ import unicode_literals

from .common import InfoExtractor
from .zdf import extract_from_xml_url


class PhoenixIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?phoenix\.de/content/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.phoenix.de/content/884301',
        'md5': 'ed249f045256150c92e72dbb70eadec6',
        'info_dict': {
            'id': '884301',
            'ext': 'mp4',
            'title': 'Michael Krons mit Hans-Werner Sinn',
            'description': 'Im Dialog - Sa. 25.10.14, 00.00 - 00.35 Uhr',
            'upload_date': '20141025',
            'uploader': 'Im Dialog',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        internal_id = self._search_regex(
            r'<div class="phx_vod" id="phx_vod_([0-9]+)"',
            webpage, 'internal video ID')

        api_url = 'http://www.phoenix.de/php/zdfplayer-v1.3/data/beitragsDetails.php?ak=web&id=%s' % internal_id
        return extract_from_xml_url(self, video_id, api_url)
