# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .nexx import NexxIE


class Tele5IE(InfoExtractor):
    _VALID_URL = r'https://www.tele5.de/[mediathek/filme-online/videos|tv/]'

    _TESTS = [{
        'url': 'https://www.tele5.de/mediathek/filme-online/videos?vid=1550589',
        'info_dict': {
            'id': '1550589',
            'ext': 'mp4',
            'upload_date': '20180822',
            'timestamp': 1534927316,
            'title': 'SchleFaZ: Atomic Shark'
        }
    }, {
        'url': 'https://www.tele5.de/tv/dark-matter/videos',
        'info_dict': {
            'id': '1548206',
            'ext': 'mp4',
            'title': 'Folge Sechsundzwanzig',
            'timestamp': 1533664358,
            'upload_date': '20180807'
        }
    }]

    def _real_extract(self, url):
        webpage = self._download_webpage(url, 'N/A')

        video_id = self._html_search_regex(
            r'id="video-player"\sdata-id="(?P<id>[0-9]+)"',
            webpage, 'id')

        return self.url_result(
            'https://api.nexx.cloud/v3/759/videos/byid/%s'
            % video_id, ie=NexxIE.ie_key())
