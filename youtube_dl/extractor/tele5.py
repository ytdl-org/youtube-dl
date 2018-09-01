# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .nexx import NexxIE


class Tele5IE(InfoExtractor):
    _VALID_URL = r'https://www.tele5.de/(mediathek/filme-online/videos|tv/).*'

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
    }, {
        'url': 'https://www.tele5.de/tv/relic-hunter/videos',
        'info_dict': {
            'id': '1548034',
            'ext': 'mp4',
            'timestamp': 1533577964,
            'upload_date': '20180806',
            'title': 'Mr. Right'
        }
    }, {
        'url': 'https://www.tele5.de/tv/buffy-im-bann-der-daemonen/videos',
        'info_dict': {
            'id': '1547129',
            'ext': 'mp4',
            'upload_date': '20180730',
            'timestamp': 1532967491,
            'title': 'Der Höllenhund'
        }
    }]

    def _real_extract(self, url):
        webpage = self._download_webpage(url, 'N/A')

        id = self._html_search_regex(
            r'class="ce_videoelementnexx-video__player"\sid="video-player"\sdata-id="(?P<id>[0-9]+)"',
            webpage, 'id')

        return self.url_result(
            'https://api.nexx.cloud/v3/759/videos/byid/%s'
            % id, ie=NexxIE.ie_key())
