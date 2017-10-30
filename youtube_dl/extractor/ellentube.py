# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    urljoin,
)


class EllenTubeBaseIE(InfoExtractor):
    API_URL = 'https://api-prod.ellentube.com/'

    def _extract_video_from_json(self, data, video_id, display_id=None):
        title = data['title']
        description = data.get('description')
        publish_time = int_or_none(data.get('publishTime'))
        thumbnail = data.get('thumbnail')

        formats = []
        duration = None
        for entry in data.get('media'):
            if entry.get('id') == 'm3u8':
                formats = self._extract_m3u8_formats(
                    entry.get('url'), video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls')
                duration = int_or_none(entry.get('duration'))
                break
        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'display_id': display_id,
            'duration': duration,
            'thumbnail': thumbnail,
            'timestamp': publish_time,
            'formats': formats,
        }

    def _extract_playlist_entries_from_json(self, data, display_id):
        return [self._extract_video_from_json(elem, elem['id'])
                for elem in data if elem.get('type') == 'VIDEO']

    def _extract_from_video_id(self, video_id, display_id=None):
        api_data = self._download_json(
            urljoin(self.API_URL, 'ellenapi/api/item/%s' % video_id), video_id)
        return self._extract_video_from_json(api_data, video_id, display_id)

    def _extract_playlist(self, url, display_id, extract_description=True):
        webpage = self._download_webpage(url, display_id)
        playlist_data = self._html_search_regex(
            r'<div\s+data-component\s*=\s*"Details"(.+)</div>', webpage, 'playlist data')
        playlist_title = self._search_regex(
            r'"title"\s*:\s*"(.+?)"', playlist_data, 'playlist title')
        playlist_description = clean_html(self._search_regex(
            r'"description"\s*:\s*"(.+?)"', playlist_data, 'playlist description',
            fatal=False)) if extract_description else None
        api_search = self._search_regex(
            r'"filter"\s*:\s*"(.+?)"', playlist_data, 'playlist api request')
        api_data = self._download_json(
            urljoin(self.API_URL, 'ellenapi/api/feed/?%s' % api_search), display_id)
        return self.playlist_result(
            self._extract_playlist_entries_from_json(api_data, display_id),
            display_id, playlist_title, playlist_description)


class EllenTubeVideoIE(EllenTubeBaseIE):
    _VALID_URL = r'https?://(?:www\.)?ellentube\.com/video/(?P<id>.+)\.html'

    _TEST = {
        'url': 'https://www.ellentube.com/video/ellen-meets-las-vegas-survivors-jesus-campos-and-stephen-schuck.html',
        'md5': '2fabc277131bddafdd120e0fc0f974c9',
        'info_dict': {
            'id': '0822171c-3829-43bf-b99f-d77358ae75e3',
            'ext': 'mp4',
            'title': 'Ellen Meets Las Vegas Survivors Jesus Campos and Stephen Schuck',
            'description': 'md5:76e3355e2242a78ad9e3858e5616923f',
            'display_id': 'ellen-meets-las-vegas-survivors-jesus-campos-and-stephen-schuck',
            'duration': 514,
            'timestamp': 1508505120000,
            'thumbnail': 'https://warnerbros-h.assetsadobe.com/is/image/content/dam/ellen/videos/episodes/season15/32/video--2728751654987218111',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id_regex = r'data-config.+([\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})'
        video_id = self._search_regex(video_id_regex, webpage, 'video id')
        return self._extract_from_video_id(video_id, display_id)


class EllenTubeEpisodeIE(EllenTubeBaseIE):
    _VALID_URL = r'https?://(?:www\.)?ellentube\.com/episode/(?P<id>.+)\.html'

    _TEST = {
        'url': 'https://www.ellentube.com/episode/dax-shepard-jordan-fisher-haim.html',
        'info_dict': {
            'id': 'dax-shepard-jordan-fisher-haim',
            'title': 'Dax Shepard, \'DWTS\' Team Jordan Fisher & Lindsay Arnold, HAIM',
            'description': 'md5:aed85d42892f6126e71ec5ed2aea2a0d'
        },
        'playlist_count': 6,
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        return self._extract_playlist(url, display_id)


class EllenTubeStudioIE(EllenTubeBaseIE):
    _VALID_URL = r'https?://(?:www\.)?ellentube\.com/studios/(?P<id>.+)\.html'

    _TEST = {
        'url': 'https://www.ellentube.com/studios/macey-goes-rving0.html',
        'info_dict': {
            'id': 'macey-goes-rving0',
            'title': 'Macey Goes RVing',
        },
        'playlist_mincount': 3,
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        return self._extract_playlist(url, display_id, False)
