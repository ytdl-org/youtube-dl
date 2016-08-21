from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import remove_end


class CharlieRoseIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?charlierose\.com/video(?:s|/player)/(?P<id>\d+)'
    _TEST = {
        'url': 'https://charlierose.com/videos/27996',
        'info_dict': {
            'id': '27996',
            'ext': 'mp4',
            'title': 'Remembering Zaha Hadid',
            'thumbnail': 're:^https?://.*\.jpg\?\d+',
            'description': 'We revisit past conversations with Zaha Hadid, in memory of the world renowned Iraqi architect.',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }

    _PLAYER_BASE = 'https://charlierose.com/video/player/%s'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(self._PLAYER_BASE % video_id, video_id)

        title = remove_end(self._og_search_title(webpage), ' - Charlie Rose')

        entries = self._parse_html5_media_entries(self._PLAYER_BASE % video_id, webpage, video_id)[0]
        formats = entries['formats']

        self._sort_formats(formats)
        self._remove_duplicate_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
            'subtitles': entries.get('subtitles'),
        }
