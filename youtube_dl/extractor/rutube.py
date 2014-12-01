# encoding: utf-8
from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor
from ..utils import (
    compat_str,
    unified_strdate,
    ExtractorError,
)


class RutubeIE(InfoExtractor):
    IE_NAME = 'rutube'
    IE_DESC = 'Rutube videos'
    _VALID_URL = r'https?://rutube\.ru/video/(?P<id>[\da-z]{32})'

    _TEST = {
        'url': 'http://rutube.ru/video/3eac3b4561676c17df9132a9a1e62e3e/',
        'info_dict': {
            'id': '3eac3b4561676c17df9132a9a1e62e3e',
            'ext': 'mp4',
            'title': 'Раненный кенгуру забежал в аптеку',
            'description': 'http://www.ntdtv.ru ',
            'duration': 80,
            'uploader': 'NTDRussian',
            'uploader_id': '29790',
            'upload_date': '20131016',
        },
        'params': {
            # It requires ffmpeg (m3u8 download)
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        video = self._download_json(
            'http://rutube.ru/api/video/%s/?format=json' % video_id,
            video_id, 'Downloading video JSON')

        # Some videos don't have the author field
        author = video.get('author') or {}

        options = self._download_json(
            'http://rutube.ru/api/play/options/%s/?format=json' % video_id,
            video_id, 'Downloading options JSON')

        m3u8_url = options['video_balancer'].get('m3u8')
        if m3u8_url is None:
            raise ExtractorError('Couldn\'t find m3u8 manifest url')
        formats = self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4')

        return {
            'id': video['id'],
            'title': video['title'],
            'description': video['description'],
            'duration': video['duration'],
            'view_count': video['hits'],
            'formats': formats,
            'thumbnail': video['thumbnail_url'],
            'uploader': author.get('name'),
            'uploader_id': compat_str(author['id']) if author else None,
            'upload_date': unified_strdate(video['created_ts']),
            'age_limit': 18 if video['is_adult'] else 0,
        }


class RutubeChannelIE(InfoExtractor):
    IE_NAME = 'rutube:channel'
    IE_DESC = 'Rutube channels'
    _VALID_URL = r'http://rutube\.ru/tags/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://rutube.ru/tags/video/1800/',
        'info_dict': {
            'id': '1800',
        },
        'playlist_mincount': 68,
    }]

    _PAGE_TEMPLATE = 'http://rutube.ru/api/tags/video/%s/?page=%s&format=json'

    def _extract_videos(self, channel_id, channel_title=None):
        entries = []
        for pagenum in itertools.count(1):
            page = self._download_json(
                self._PAGE_TEMPLATE % (channel_id, pagenum),
                channel_id, 'Downloading page %s' % pagenum)
            results = page['results']
            if not results:
                break
            entries.extend(self.url_result(result['video_url'], 'Rutube') for result in results)
            if not page['has_next']:
                break
        return self.playlist_result(entries, channel_id, channel_title)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        channel_id = mobj.group('id')
        return self._extract_videos(channel_id)


class RutubeMovieIE(RutubeChannelIE):
    IE_NAME = 'rutube:movie'
    IE_DESC = 'Rutube movies'
    _VALID_URL = r'http://rutube\.ru/metainfo/tv/(?P<id>\d+)'
    _TESTS = []

    _MOVIE_TEMPLATE = 'http://rutube.ru/api/metainfo/tv/%s/?format=json'
    _PAGE_TEMPLATE = 'http://rutube.ru/api/metainfo/tv/%s/video?page=%s&format=json'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        movie_id = mobj.group('id')
        movie = self._download_json(
            self._MOVIE_TEMPLATE % movie_id, movie_id,
            'Downloading movie JSON')
        movie_name = movie['name']
        return self._extract_videos(movie_id, movie_name)


class RutubePersonIE(RutubeChannelIE):
    IE_NAME = 'rutube:person'
    IE_DESC = 'Rutube person videos'
    _VALID_URL = r'http://rutube\.ru/video/person/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://rutube.ru/video/person/313878/',
        'info_dict': {
            'id': '313878',
        },
        'playlist_mincount': 37,
    }]

    _PAGE_TEMPLATE = 'http://rutube.ru/api/video/person/%s/?page=%s&format=json'
