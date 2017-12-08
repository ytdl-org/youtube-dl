# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
)


class EllenTubeIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    (?:
                        https://api-prod\.ellentube\.com/ellenapi/api/item/
                        |ellentube:
                    )
                    (?P<id>
                        [\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}
                    )'''

    _TESTS = [{
        'url': 'https://api-prod.ellentube.com/ellenapi/api/item/75c64c16-aefd-4558-b4f5-3de09b22e6fc',
        'match_only': True,
    }, {
        'url': 'ellentube:734a3353-f697-4e79-9ca9-bfc3002dc1e0',
        'match_only': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            'https://api-prod.ellentube.com/ellenapi/api/item/%s' % video_id, video_id)
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
            'duration': duration,
            'thumbnail': thumbnail,
            'timestamp': publish_time,
            'formats': formats,
        }


class EllenTubeVideoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ellentube\.com/video/(?P<id>.+)\.html'

    _TEST = {
        'url': 'https://www.ellentube.com/video/ellen-meets-las-vegas-survivors-jesus-campos-and-stephen-schuck.html',
        'md5': '2fabc277131bddafdd120e0fc0f974c9',
        'info_dict': {
            'id': '0822171c-3829-43bf-b99f-d77358ae75e3',
            'ext': 'mp4',
            'title': 'Ellen Meets Las Vegas Survivors Jesus Campos and Stephen Schuck',
            'description': 'md5:76e3355e2242a78ad9e3858e5616923f',
            'duration': 514,
            'timestamp': 1508505120000,
            'thumbnail': 'https://warnerbros-h.assetsadobe.com/is/image/content/dam/ellen/videos/episodes/season15/32/video--2728751654987218111',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._html_search_regex(
            r'(?s)<!--\s*CONTENT\s*-->.*data-config.+([\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})',
            webpage, 'video id')
        return self.url_result('ellentube:%s' % video_id, 'EllenTube')


class EllenTubePlaylistIE(InfoExtractor):
    def _extract_videos_from_json(self, data, display_id):
        return [self.url_result('ellentube:%s' % elem['id'], 'EllenTube')
                for elem in data if elem.get('type') == 'VIDEO']

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
            'https://api-prod.ellentube.com/ellenapi/api/feed/?%s' % api_search,
            display_id)
        return self.playlist_result(
            self._extract_videos_from_json(api_data, display_id),
            display_id, playlist_title, playlist_description)


class EllenTubeEpisodeIE(EllenTubePlaylistIE):
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


class EllenTubeStudioIE(EllenTubePlaylistIE):
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
