# coding: utf-8
from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_parse_qs,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    determine_ext,
    bool_or_none,
    int_or_none,
    try_get,
    unified_timestamp,
    url_or_none,
)


class RutubeBaseIE(InfoExtractor):
    def _extract_video(self, video, video_id=None, require_title=True):
        title = video['title'] if require_title else video.get('title')

        age_limit = video.get('is_adult')
        if age_limit is not None:
            age_limit = 18 if age_limit is True else 0

        uploader_id = try_get(video, lambda x: x['author']['id'])
        category = try_get(video, lambda x: x['category']['name'])

        return {
            'id': video.get('id') or video_id,
            'title': title,
            'description': video.get('description'),
            'thumbnail': video.get('thumbnail_url'),
            'duration': int_or_none(video.get('duration')),
            'uploader': try_get(video, lambda x: x['author']['name']),
            'uploader_id': compat_str(uploader_id) if uploader_id else None,
            'timestamp': unified_timestamp(video.get('created_ts')),
            'category': [category] if category else None,
            'age_limit': age_limit,
            'view_count': int_or_none(video.get('hits')),
            'comment_count': int_or_none(video.get('comments_count')),
            'is_live': bool_or_none(video.get('is_livestream')),
        }


class RutubeIE(RutubeBaseIE):
    IE_NAME = 'rutube'
    IE_DESC = 'Rutube videos'
    _VALID_URL = r'https?://rutube\.ru/(?:video|(?:play/)?embed)/(?P<id>[\da-z]{32})'

    _TESTS = [{
        'url': 'http://rutube.ru/video/3eac3b4561676c17df9132a9a1e62e3e/',
        'md5': '79938ade01294ef7e27574890d0d3769',
        'info_dict': {
            'id': '3eac3b4561676c17df9132a9a1e62e3e',
            'ext': 'flv',
            'title': 'Раненный кенгуру забежал в аптеку',
            'description': 'http://www.ntdtv.ru ',
            'duration': 80,
            'uploader': 'NTDRussian',
            'uploader_id': '29790',
            'timestamp': 1381943602,
            'upload_date': '20131016',
            'age_limit': 0,
        },
    }, {
        'url': 'http://rutube.ru/play/embed/a10e53b86e8f349080f718582ce4c661',
        'only_matching': True,
    }, {
        'url': 'http://rutube.ru/embed/a10e53b86e8f349080f718582ce4c661',
        'only_matching': True,
    }, {
        'url': 'http://rutube.ru/video/3eac3b4561676c17df9132a9a1e62e3e/?pl_id=4252',
        'only_matching': True,
    }, {
        'url': 'https://rutube.ru/video/10b3a03fc01d5bbcc632a2f3514e8aab/?pl_type=source',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if RutubePlaylistIE.suitable(url) else super(RutubeIE, cls).suitable(url)

    @staticmethod
    def _extract_urls(webpage):
        return [mobj.group('url') for mobj in re.finditer(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//rutube\.ru/embed/[\da-z]{32}.*?)\1',
            webpage)]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            'http://rutube.ru/api/video/%s/?format=json' % video_id,
            video_id, 'Downloading video JSON')

        info = self._extract_video(video, video_id)

        options = self._download_json(
            'http://rutube.ru/api/play/options/%s/?format=json' % video_id,
            video_id, 'Downloading options JSON',
            headers=self.geo_verification_headers())

        formats = []
        for format_id, format_url in options['video_balancer'].items():
            ext = determine_ext(format_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', m3u8_id=format_id, fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    format_url, video_id, f4m_id=format_id, fatal=False))
            else:
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                })
        self._sort_formats(formats)

        info['formats'] = formats
        return info


class RutubeEmbedIE(InfoExtractor):
    IE_NAME = 'rutube:embed'
    IE_DESC = 'Rutube embedded videos'
    _VALID_URL = r'https?://rutube\.ru/(?:video|play)/embed/(?P<id>[0-9]+)'

    _TESTS = [{
        'url': 'http://rutube.ru/video/embed/6722881?vk_puid37=&vk_puid38=',
        'info_dict': {
            'id': 'a10e53b86e8f349080f718582ce4c661',
            'ext': 'flv',
            'timestamp': 1387830582,
            'upload_date': '20131223',
            'uploader_id': '297833',
            'description': 'Видео группы ★http://vk.com/foxkidsreset★ музей Fox Kids и Jetix<br/><br/> восстановлено и сделано в шикоформате subziro89 http://vk.com/subziro89',
            'uploader': 'subziro89 ILya',
            'title': 'Мистический городок Эйри в Индиан 5 серия озвучка subziro89',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://rutube.ru/play/embed/8083783',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        embed_id = self._match_id(url)
        webpage = self._download_webpage(url, embed_id)

        canonical_url = self._html_search_regex(
            r'<link\s+rel="canonical"\s+href="([^"]+?)"', webpage,
            'Canonical URL')
        return self.url_result(canonical_url, RutubeIE.ie_key())


class RutubePlaylistBaseIE(RutubeBaseIE):
    def _next_page_url(self, page_num, playlist_id, *args, **kwargs):
        return self._PAGE_TEMPLATE % (playlist_id, page_num)

    def _entries(self, playlist_id, *args, **kwargs):
        next_page_url = None
        for pagenum in itertools.count(1):
            page = self._download_json(
                next_page_url or self._next_page_url(
                    pagenum, playlist_id, *args, **kwargs),
                playlist_id, 'Downloading page %s' % pagenum)

            results = page.get('results')
            if not results or not isinstance(results, list):
                break

            for result in results:
                video_url = url_or_none(result.get('video_url'))
                if not video_url:
                    continue
                entry = self._extract_video(result, require_title=False)
                entry.update({
                    '_type': 'url',
                    'url': video_url,
                    'ie_key': RutubeIE.ie_key(),
                })
                yield entry

            next_page_url = page.get('next')
            if not next_page_url or not page.get('has_next'):
                break

    def _extract_playlist(self, playlist_id, *args, **kwargs):
        return self.playlist_result(
            self._entries(playlist_id, *args, **kwargs),
            playlist_id, kwargs.get('playlist_name'))

    def _real_extract(self, url):
        return self._extract_playlist(self._match_id(url))


class RutubeChannelIE(RutubePlaylistBaseIE):
    IE_NAME = 'rutube:channel'
    IE_DESC = 'Rutube channels'
    _VALID_URL = r'https?://rutube\.ru/tags/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://rutube.ru/tags/video/1800/',
        'info_dict': {
            'id': '1800',
        },
        'playlist_mincount': 68,
    }]

    _PAGE_TEMPLATE = 'http://rutube.ru/api/tags/video/%s/?page=%s&format=json'


class RutubeMovieIE(RutubePlaylistBaseIE):
    IE_NAME = 'rutube:movie'
    IE_DESC = 'Rutube movies'
    _VALID_URL = r'https?://rutube\.ru/metainfo/tv/(?P<id>\d+)'
    _TESTS = []

    _MOVIE_TEMPLATE = 'http://rutube.ru/api/metainfo/tv/%s/?format=json'
    _PAGE_TEMPLATE = 'http://rutube.ru/api/metainfo/tv/%s/video?page=%s&format=json'

    def _real_extract(self, url):
        movie_id = self._match_id(url)
        movie = self._download_json(
            self._MOVIE_TEMPLATE % movie_id, movie_id,
            'Downloading movie JSON')
        return self._extract_playlist(
            movie_id, playlist_name=movie.get('name'))


class RutubePersonIE(RutubePlaylistBaseIE):
    IE_NAME = 'rutube:person'
    IE_DESC = 'Rutube person videos'
    _VALID_URL = r'https?://rutube\.ru/video/person/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://rutube.ru/video/person/313878/',
        'info_dict': {
            'id': '313878',
        },
        'playlist_mincount': 37,
    }]

    _PAGE_TEMPLATE = 'http://rutube.ru/api/video/person/%s/?page=%s&format=json'


class RutubePlaylistIE(RutubePlaylistBaseIE):
    IE_NAME = 'rutube:playlist'
    IE_DESC = 'Rutube playlists'
    _VALID_URL = r'https?://rutube\.ru/(?:video|(?:play/)?embed)/[\da-z]{32}/\?.*?\bpl_id=(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://rutube.ru/video/cecd58ed7d531fc0f3d795d51cee9026/?pl_id=3097&pl_type=tag',
        'info_dict': {
            'id': '3097',
        },
        'playlist_count': 27,
    }, {
        'url': 'https://rutube.ru/video/10b3a03fc01d5bbcc632a2f3514e8aab/?pl_id=4252&pl_type=source',
        'only_matching': True,
    }]

    _PAGE_TEMPLATE = 'http://rutube.ru/api/playlist/%s/%s/?page=%s&format=json'

    @classmethod
    def suitable(cls, url):
        if not super(RutubePlaylistIE, cls).suitable(url):
            return False
        params = compat_parse_qs(compat_urllib_parse_urlparse(url).query)
        return params.get('pl_type', [None])[0] and int_or_none(params.get('pl_id', [None])[0])

    def _next_page_url(self, page_num, playlist_id, item_kind):
        return self._PAGE_TEMPLATE % (item_kind, playlist_id, page_num)

    def _real_extract(self, url):
        qs = compat_parse_qs(compat_urllib_parse_urlparse(url).query)
        playlist_kind = qs['pl_type'][0]
        playlist_id = qs['pl_id'][0]
        return self._extract_playlist(playlist_id, item_kind=playlist_kind)
