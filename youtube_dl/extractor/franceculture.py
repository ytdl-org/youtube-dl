# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    unified_strdate,
)


class FranceCultureIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?franceculture\.fr/emissions/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'http://www.franceculture.fr/emissions/carnet-nomade/rendez-vous-au-pays-des-geeks',
        'info_dict': {
            'id': 'rendez-vous-au-pays-des-geeks',
            'display_id': 'rendez-vous-au-pays-des-geeks',
            'ext': 'mp3',
            'title': 'Rendez-vous au pays des geeks',
            'thumbnail': 're:^https?://.*\\.jpg$',
            'upload_date': '20140301',
            'vcodec': 'none',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_url = self._search_regex(
            r'(?s)<div[^>]+class="[^"]*?title-zone-diffusion[^"]*?"[^>]*>.*?<button[^>]+data-asset-source="([^"]+)"',
            webpage, 'video path')

        title = self._og_search_title(webpage)

        upload_date = unified_strdate(self._search_regex(
            '(?s)<div[^>]+class="date"[^>]*>.*?<span[^>]+class="inner"[^>]*>([^<]+)<',
            webpage, 'upload date', fatal=False))
        thumbnail = self._search_regex(
            r'(?s)<figure[^>]+itemtype="https://schema.org/ImageObject"[^>]*>.*?<img[^>]+data-dejavu-src="([^"]+)"',
            webpage, 'thumbnail', fatal=False)
        uploader = self._html_search_regex(
            r'(?s)<div id="emission".*?<span class="author">(.*?)</span>',
            webpage, 'uploader', default=None)
        vcodec = 'none' if determine_ext(video_url.lower()) == 'mp3' else None

        return {
            'id': display_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'vcodec': vcodec,
            'uploader': uploader,
            'upload_date': upload_date,
        }
