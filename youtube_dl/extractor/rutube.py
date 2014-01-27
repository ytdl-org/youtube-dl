# encoding: utf-8
from __future__ import unicode_literals

import re
import json
import itertools

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    compat_str,
    ExtractorError,
)


class RutubeIE(InfoExtractor):
    IE_NAME = 'rutube'
    IE_DESC = 'Rutube videos'    
    _VALID_URL = r'https?://rutube\.ru/video/(?P<long_id>\w+)'

    _TEST = {
        'url': 'http://rutube.ru/video/3eac3b4561676c17df9132a9a1e62e3e/',
        'file': '3eac3b4561676c17df9132a9a1e62e3e.mp4',
        'info_dict': {
            'title': 'Раненный кенгуру забежал в аптеку',
            'uploader': 'NTDRussian',
            'uploader_id': '29790',
        },
        'params': {
            # It requires ffmpeg (m3u8 download)
            'skip_download': True,
        },
    }

    def _get_api_response(self, short_id, subpath):
        api_url = 'http://rutube.ru/api/play/%s/%s/?format=json' % (subpath, short_id)
        response_json = self._download_webpage(api_url, short_id,
            'Downloading %s json' % subpath)
        return json.loads(response_json)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        long_id = mobj.group('long_id')
        webpage = self._download_webpage(url, long_id)
        og_video = self._og_search_video_url(webpage)
        short_id = compat_urlparse.urlparse(og_video).path[1:]
        options = self._get_api_response(short_id, 'options')
        trackinfo = self._get_api_response(short_id, 'trackinfo')
        # Some videos don't have the author field
        author = trackinfo.get('author') or {}
        m3u8_url = trackinfo['video_balancer'].get('m3u8')
        if m3u8_url is None:
            raise ExtractorError('Couldn\'t find m3u8 manifest url')

        return {
            'id': trackinfo['id'],
            'title': trackinfo['title'],
            'url': m3u8_url,
            'ext': 'mp4',
            'thumbnail': options['thumbnail_url'],
            'uploader': author.get('name'),
            'uploader_id': compat_str(author['id']) if author else None,
        }


class RutubeChannelIE(InfoExtractor):
    IE_NAME = 'rutube:channel'
    IE_DESC = 'Rutube channels'    
    _VALID_URL = r'http://rutube\.ru/tags/video/(?P<id>\d+)'

    _PAGE_TEMPLATE = 'http://rutube.ru/api/tags/video/%s/?page=%s&format=json'

    def _extract_videos(self, channel_id, channel_title=None):
        entries = []
        for pagenum in itertools.count(1):
            response_json = self._download_webpage(self._PAGE_TEMPLATE % (channel_id, pagenum),
                                                   channel_id, 'Downloading page %s' % pagenum)
            page = json.loads(response_json)
            if 'detail' in page and page['detail'] == 'Not found':
                raise ExtractorError('Channel %s does not exist' % channel_id, expected=True)
            results = page['results']
            if len(results) == 0:
                break;
            entries.extend(self.url_result(v['video_url'], 'Rutube') for v in results)
            if page['has_next'] is False:
                break;
        return self.playlist_result(entries, channel_id, channel_title)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        channel_id = mobj.group('id')
        return self._extract_videos(channel_id)


class RutubeMovieIE(RutubeChannelIE):
    IE_NAME = 'rutube:movie'
    IE_DESC = 'Rutube movies'    
    _VALID_URL = r'http://rutube\.ru/metainfo/tv/(?P<id>\d+)'

    _MOVIE_TEMPLATE = 'http://rutube.ru/api/metainfo/tv/%s/?format=json'
    _PAGE_TEMPLATE = 'http://rutube.ru/api/metainfo/tv/%s/video?page=%s&format=json'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        movie_id = mobj.group('id')
        movie_json = self._download_webpage(self._MOVIE_TEMPLATE % movie_id, movie_id,
                                            'Downloading movie JSON')
        movie = json.loads(movie_json)
        if 'detail' in movie and movie['detail'] == 'Not found':
            raise ExtractorError('Movie %s does not exist' % movie_id, expected=True)
        movie_name = movie['name']
        return self._extract_videos(movie_id, movie_name)