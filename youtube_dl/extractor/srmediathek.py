# encoding: utf-8
from __future__ import unicode_literals

from .ard import ARDMediathekIE
from ..utils import (
    ExtractorError,
    get_element_by_attribute,
)


class SRMediathekIE(ARDMediathekIE):
    IE_DESC = 'Saarländischer Rundfunk'
    _VALID_URL = r'https?://sr-mediathek\.sr-online\.de/index\.php\?.*?&id=(?P<id>[0-9]+)'

    _TESTS = [{
        'url': 'http://sr-mediathek.sr-online.de/index.php?seite=7&id=28455',
        'info_dict': {
            'id': '28455',
            'ext': 'mp4',
            'title': 'sportarena (26.10.2014)',
            'description': 'Ringen: KSV Köllerbach gegen Aachen-Walheim; Frauen-Fußball: 1. FC Saarbrücken gegen Sindelfingen; Motorsport: Rallye in Losheim; dazu: Interview mit Timo Bernhard; Turnen: TG Saar; Reitsport: Deutscher Voltigier-Pokal; Badminton: Interview mit Michael Fuchs ',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
        'skip': 'no longer available',
    }, {
        'url': 'http://sr-mediathek.sr-online.de/index.php?seite=7&id=37682',
        'info_dict': {
            'id': '37682',
            'ext': 'mp4',
            'title': 'Love, Cakes and Rock\'n\'Roll',
            'description': 'md5:18bf9763631c7d326c22603681e1123d',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'expected_warnings': ['Unable to download f4m manifest']
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if '>Der gew&uuml;nschte Beitrag ist leider nicht mehr verf&uuml;gbar.<' in webpage:
            raise ExtractorError('Video %s is no longer available' % video_id, expected=True)

        media_collection_url = self._search_regex(
            r'data-mediacollection-ardplayer="([^"]+)"', webpage, 'media collection url')
        info = self._extract_media_info(media_collection_url, webpage, video_id)
        info.update({
            'id': video_id,
            'title': get_element_by_attribute('class', 'ardplayer-title', webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        })
        return info
