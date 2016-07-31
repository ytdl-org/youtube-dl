from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    clean_html,
    get_element_by_class,
)


class NobelprizeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nobelprize\.org/mediaplayer/.+?id=(?P<id>[0-9]{4})'
    IE_DESC = 'Nobelprize'

    _TEST = {
        'url': 'https://www.nobelprize.org/mediaplayer/index.php?id=2028',
        'md5': '19bb7134879a6e8f0731235f3c076321',
        'info_dict': {
            'id': '2028',
            'ext': 'mp4',
            'title': 'Acceptance Speech by Elie Wiesel (18 minutes)'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, id)

        # we now do a regex search for a JS variable in our webpage
        # which will deliver us a m3u8 file with all streams available

        m3u8_playlist = self._search_regex(
            r"(http://nobelvod-vh.akamaihd.net/i/flashcontent/.+master\.m3u8)",
            webpage,
            'm3u8 url',
        )

        formats = self._extract_m3u8_formats(m3u8_playlist, video_id, 'mp4')

        return {
            'id': video_id,
            'title': clean_html(get_element_by_class('video-headline', webpage)),
            'formats': formats,
        }
