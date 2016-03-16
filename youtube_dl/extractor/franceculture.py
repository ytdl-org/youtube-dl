# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
)
from ..utils import (
    determine_ext,
    int_or_none,
    ExtractorError,
)


class FranceCultureIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?franceculture\.fr/player/reecouter\?play=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.franceculture.fr/player/reecouter?play=4795174',
        'info_dict': {
            'id': '4795174',
            'ext': 'mp3',
            'title': 'Rendez-vous au pays des geeks',
            'alt_title': 'Carnet nomade | 13-14',
            'vcodec': 'none',
            'upload_date': '20140301',
            'thumbnail': r're:^http://static\.franceculture\.fr/.*/images/player/Carnet-nomade\.jpg$',
            'description': 'startswith:Avec :Jean-Baptiste Péretié pour son documentaire sur Arte "La revanche',
            'timestamp': 1393700400,
        }
    }

    def _extract_from_player(self, url, video_id):
        webpage = self._download_webpage(url, video_id)

        video_path = self._search_regex(
            r'<a id="player".*?href="([^"]+)"', webpage, 'video path')
        video_url = compat_urlparse.urljoin(url, video_path)
        timestamp = int_or_none(self._search_regex(
            r'<a id="player".*?data-date="([0-9]+)"',
            webpage, 'upload date', fatal=False))
        thumbnail = self._search_regex(
            r'<a id="player".*?>\s+<img src="([^"]+)"',
            webpage, 'thumbnail', fatal=False)

        display_id = self._search_regex(
            r'<span class="path-diffusion">emission-(.*?)</span>', webpage, 'display_id')

        title = self._html_search_regex(
            r'<span class="title-diffusion">(.*?)</span>', webpage, 'title')
        alt_title = self._html_search_regex(
            r'<span class="title">(.*?)</span>',
            webpage, 'alt_title', fatal=False)
        description = self._html_search_regex(
            r'<span class="description">(.*?)</span>',
            webpage, 'description', fatal=False)

        uploader = self._html_search_regex(
            r'(?s)<div id="emission".*?<span class="author">(.*?)</span>',
            webpage, 'uploader', default=None)
        vcodec = 'none' if determine_ext(video_url.lower()) == 'mp3' else None

        return {
            'id': video_id,
            'url': video_url,
            'vcodec': vcodec,
            'uploader': uploader,
            'timestamp': timestamp,
            'title': title,
            'alt_title': alt_title,
            'thumbnail': thumbnail,
            'description': description,
            'display_id': display_id,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self._extract_from_player(url, video_id)


class FranceCultureEmissionIE(FranceCultureIE):
    _VALID_URL = r'https?://(?:www\.)?franceculture\.fr/emission-(?P<id>[^?#]+)'
    _TEST = {
        'url': 'http://www.franceculture.fr/emission-les-carnets-de-la-creation-jean-gabriel-periot-cineaste-2015-10-13',
        'info_dict': {
            'title': 'Jean-Gabriel Périot, cinéaste',
            'alt_title': 'Les Carnets de la création',
            'id': '5093239',
            'display_id': 'les-carnets-de-la-creation-jean-gabriel-periot-cineaste-2015-10-13',
            'ext': 'mp3',
            'timestamp': 1444762500,
            'upload_date': '20151013',
            'description': 'startswith:Aujourd\'hui dans "Les carnets de la création", le cinéaste',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_path = self._html_search_regex(
            r'<a class="rf-player-open".*?href="([^"]+)"', webpage, 'video path', 'no_path_player')
        if video_path == 'no_path_player':
            raise ExtractorError('no player : no sound in this page.', expected=True)
        new_id = self._search_regex('play=(?P<id>[0-9]+)', video_path, 'new_id', group='id')
        video_url = compat_urlparse.urljoin(url, video_path)
        return self._extract_from_player(video_url, new_id)
