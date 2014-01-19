# encoding: utf-8

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urllib_request,
    ExtractorError,
)


class IviIE(InfoExtractor):
    IE_DESC = u'ivi.ru'
    IE_NAME = u'ivi'
    _VALID_URL = r'^https?://(?:www\.)?ivi\.ru/watch(?:/(?P<compilationid>[^/]+))?/(?P<videoid>\d+)'

    _TESTS = [
        # Single movie
        {
            u'url': u'http://www.ivi.ru/watch/53141',
            u'file': u'53141.mp4',
            u'md5': u'6ff5be2254e796ed346251d117196cf4',
            u'info_dict': {
                u'title': u'Иван Васильевич меняет профессию',
                u'description': u'md5:14d8eda24e9d93d29b5857012c6d6346',
                u'duration': 5498,
                u'thumbnail': u'http://thumbs.ivi.ru/f20.vcp.digitalaccess.ru/contents/d/1/c3c885163a082c29bceeb7b5a267a6.jpg',
            },
            u'skip': u'Only works from Russia',
        },
        # Serial's serie
        {
            u'url': u'http://www.ivi.ru/watch/dezhurnyi_angel/74791',
            u'file': u'74791.mp4',
            u'md5': u'3e6cc9a848c1d2ebcc6476444967baa9',
            u'info_dict': {
                u'title': u'Дежурный ангел - 1 серия',
                u'duration': 2490,
                u'thumbnail': u'http://thumbs.ivi.ru/f7.vcp.digitalaccess.ru/contents/8/e/bc2f6c2b6e5d291152fdd32c059141.jpg',
            },
            u'skip': u'Only works from Russia',
         }
    ]
    
    # Sorted by quality
    _known_formats = ['MP4-low-mobile', 'MP4-mobile', 'FLV-lo', 'MP4-lo', 'FLV-hi', 'MP4-hi', 'MP4-SHQ']

    # Sorted by size
    _known_thumbnails = ['Thumb-120x90', 'Thumb-160', 'Thumb-640x480']

    def _extract_description(self, html):
        m = re.search(r'<meta name="description" content="(?P<description>[^"]+)"/>', html)
        return m.group('description') if m is not None else None

    def _extract_comment_count(self, html):
        m = re.search(u'(?s)<a href="#" id="view-comments" class="action-button dim gradient">\s*Комментарии:\s*(?P<commentcount>\d+)\s*</a>', html)
        return int(m.group('commentcount')) if m is not None else 0

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        api_url = 'http://api.digitalaccess.ru/api/json/'

        data = {u'method': u'da.content.get',
                u'params': [video_id, {u'site': u's183',
                                       u'referrer': u'http://www.ivi.ru/watch/%s' % video_id,
                                       u'contentid': video_id
                                    }
                            ]
                }

        request = compat_urllib_request.Request(api_url, json.dumps(data))

        video_json_page = self._download_webpage(request, video_id, u'Downloading video JSON')
        video_json = json.loads(video_json_page)

        if u'error' in video_json:
            error = video_json[u'error']
            if error[u'origin'] == u'NoRedisValidData':
                raise ExtractorError(u'Video %s does not exist' % video_id, expected=True)
            raise ExtractorError(u'Unable to download video %s: %s' % (video_id, error[u'message']), expected=True)

        result = video_json[u'result']

        formats = [{
            'url': x[u'url'],
            'format_id': x[u'content_format'],
            'preference': self._known_formats.index(x[u'content_format']),
        } for x in result[u'files'] if x[u'content_format'] in self._known_formats]

        self._sort_formats(formats)

        if not formats:
            raise ExtractorError(u'No media links available for %s' % video_id)

        duration = result[u'duration']
        compilation = result[u'compilation']
        title = result[u'title']

        title = '%s - %s' % (compilation, title) if compilation is not None else title  

        previews = result[u'preview']
        previews.sort(key=lambda fmt: self._known_thumbnails.index(fmt['content_format']))
        thumbnail = previews[-1][u'url'] if len(previews) > 0 else None

        video_page = self._download_webpage(url, video_id, u'Downloading video page')
        description = self._extract_description(video_page)
        comment_count = self._extract_comment_count(video_page)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'description': description,
            'duration': duration,
            'comment_count': comment_count,
            'formats': formats,
        }


class IviCompilationIE(InfoExtractor):
    IE_DESC = u'ivi.ru compilations'
    IE_NAME = u'ivi:compilation'
    _VALID_URL = r'^https?://(?:www\.)?ivi\.ru/watch/(?!\d+)(?P<compilationid>[a-z\d_-]+)(?:/season(?P<seasonid>\d+))?$'

    def _extract_entries(self, html, compilation_id):
        return [self.url_result('http://www.ivi.ru/watch/%s/%s' % (compilation_id, serie), 'Ivi')
                for serie in re.findall(r'<strong><a href="/watch/%s/(\d+)">(?:[^<]+)</a></strong>' % compilation_id, html)]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        compilation_id = mobj.group('compilationid')
        season_id = mobj.group('seasonid')

        if season_id is not None: # Season link
            season_page = self._download_webpage(url, compilation_id, u'Downloading season %s web page' % season_id)
            playlist_id = '%s/season%s' % (compilation_id, season_id)
            playlist_title = self._html_search_meta(u'title', season_page, u'title')
            entries = self._extract_entries(season_page, compilation_id)
        else: # Compilation link            
            compilation_page = self._download_webpage(url, compilation_id, u'Downloading compilation web page')
            playlist_id = compilation_id
            playlist_title = self._html_search_meta(u'title', compilation_page, u'title')
            seasons = re.findall(r'<a href="/watch/%s/season(\d+)">[^<]+</a>' % compilation_id, compilation_page)
            if len(seasons) == 0: # No seasons in this compilation
                entries = self._extract_entries(compilation_page, compilation_id)
            else:
                entries = []
                for season_id in seasons:
                    season_page = self._download_webpage('http://www.ivi.ru/watch/%s/season%s' % (compilation_id, season_id),
                                                         compilation_id, u'Downloading season %s web page' % season_id)
                    entries.extend(self._extract_entries(season_page, compilation_id))

        return self.playlist_result(entries, playlist_id, playlist_title)