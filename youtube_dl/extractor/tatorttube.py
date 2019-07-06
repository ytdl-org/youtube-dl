# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class TatortTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tatort\.tube/Stream/.*-(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.tatort.tube/Stream/Taxi-nach-Leipzig-1',
        'info_dict': {
            'id': '1',
            'ext': 'mp4',
            'title': 'Taxi-nach-Leipzig',
            'description': 'Tatort: Taxi nach Leipzig (Folge 1, 1970) Jetzt Kostenlos streamen! '
                           'Ein Fernschreiben des Generalstaatsanwalts der DDR fordert die '
                           'Strafverfolgungsbehörden der Bundesrepublik zur Mithilfe bei der '
                           'Klärung eines Falles auf. An einem Autobahnrastplatz bei Leipzig '
                           'ist die Leiche eines Jungen gefunden worden, der Schuhe...',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': False,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._search_regex(r'(content\=\"http\:\/\/www\.tatort\.tube\/Stream\/)([\w+\-]+)-([0-9]+)(\"\spr)', webpage, 'title', group=2)
        description = self._og_search_description(webpage)
        token = self._search_regex(r'\.mp4/master\.m3u8\?tkn\=([\w|\-]+)\&exp\=(\d+)', webpage, 'token', group=1)
        tokenExpires = self._search_regex(r'\.mp4/master\.m3u8\?tkn\=([\w|\-]+)\&exp\=(\d+)', webpage, 'tokenExpires', group=2)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': [{
                'format_id': 'hsl',
                'ext': 'mp4',
                'url': 'https://cdn.tatort.tube/hls/' + video_id + '.mp4/master.m3u8?tkn=' + token + '&exp=' + tokenExpires,
            }],
            'thumbnail': 'https://www.tatort.tube/images/folge/' + video_id + '.jpg',
        }
