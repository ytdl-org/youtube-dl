# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class BpbIE(InfoExtractor):
    IE_DESC = 'Bundeszentrale für politische Bildung'
    _VALID_URL = r'http://www\.bpb\.de/mediathek/(?P<id>[0-9]+)/'

    _TEST = {
        'url': 'http://www.bpb.de/mediathek/297/joachim-gauck-zu-1989-und-die-erinnerung-an-die-ddr',
        'md5': '0792086e8e2bfbac9cdf27835d5f2093',
        'info_dict': {
            'id': '297',
            'ext': 'mp4',
            'title': 'Joachim Gauck zu 1989 und die Erinnerung an die DDR',
            'description': 'Joachim Gauck, erster Beauftragter für die Stasi-Unterlagen, spricht auf dem Geschichtsforum über die friedliche Revolution 1989 und eine "gewisse Traurigkeit" im Umgang mit der DDR-Vergangenheit.'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<h2 class="white">(.*?)</h2>', webpage, 'title')
        video_url = self._html_search_regex(
            r'(http://film\.bpb\.de/player/dokument_[0-9]+\.mp4)',
            webpage, 'video URL')

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': self._og_search_description(webpage),
        }
