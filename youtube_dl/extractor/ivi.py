# encoding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import (
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
)


class IviIE(InfoExtractor):
    IE_DESC = 'ivi.ru'
    IE_NAME = 'ivi'
    _VALID_URL = r'https?://(?:www\.)?ivi\.ru/(?:watch/(?:[^/]+/)?|video/player\?.*?videoId=)(?P<id>\d+)'

    _TESTS = [
        # Single movie
        {
            'url': 'http://www.ivi.ru/watch/53141',
            'md5': '6ff5be2254e796ed346251d117196cf4',
            'info_dict': {
                'id': '53141',
                'ext': 'mp4',
                'title': 'Иван Васильевич меняет профессию',
                'description': 'md5:b924063ea1677c8fe343d8a72ac2195f',
                'duration': 5498,
                'thumbnail': 'http://thumbs.ivi.ru/f20.vcp.digitalaccess.ru/contents/d/1/c3c885163a082c29bceeb7b5a267a6.jpg',
            },
            'skip': 'Only works from Russia',
        },
        # Serial's serie
        {
            'url': 'http://www.ivi.ru/watch/dvoe_iz_lartsa/9549',
            'md5': '221f56b35e3ed815fde2df71032f4b3e',
            'info_dict': {
                'id': '9549',
                'ext': 'mp4',
                'title': 'Двое из ларца - Серия 1',
                'duration': 2655,
                'thumbnail': 'http://thumbs.ivi.ru/f15.vcp.digitalaccess.ru/contents/8/4/0068dc0677041f3336b7c2baad8fc0.jpg',
            },
            'skip': 'Only works from Russia',
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
        m = re.search('(?s)<a href="#" id="view-comments" class="action-button dim gradient">\s*Комментарии:\s*(?P<commentcount>\d+)\s*</a>', html)
        return int(m.group('commentcount')) if m is not None else 0

    def _real_extract(self, url):
        video_id = self._match_id(url)

        api_url = 'http://api.digitalaccess.ru/api/json/'

        data = {
            'method': 'da.content.get',
            'params': [
                video_id, {
                    'site': 's183',
                    'referrer': 'http://www.ivi.ru/watch/%s' % video_id,
                    'contentid': video_id
                }
            ]
        }

        request = compat_urllib_request.Request(api_url, json.dumps(data))

        video_json_page = self._download_webpage(
            request, video_id, 'Downloading video JSON')
        video_json = json.loads(video_json_page)

        if 'error' in video_json:
            error = video_json['error']
            if error['origin'] == 'NoRedisValidData':
                raise ExtractorError('Video %s does not exist' % video_id, expected=True)
            raise ExtractorError(
                'Unable to download video %s: %s' % (video_id, error['message']),
                expected=True)

        result = video_json['result']

        formats = [{
            'url': x['url'],
            'format_id': x['content_format'],
            'preference': self._known_formats.index(x['content_format']),
        } for x in result['files'] if x['content_format'] in self._known_formats]

        self._sort_formats(formats)

        if not formats:
            raise ExtractorError('No media links available for %s' % video_id)

        duration = result['duration']
        compilation = result['compilation']
        title = result['title']

        title = '%s - %s' % (compilation, title) if compilation is not None else title

        previews = result['preview']
        previews.sort(key=lambda fmt: self._known_thumbnails.index(fmt['content_format']))
        thumbnail = previews[-1]['url'] if len(previews) > 0 else None

        video_page = self._download_webpage(url, video_id, 'Downloading video page')
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
    IE_DESC = 'ivi.ru compilations'
    IE_NAME = 'ivi:compilation'
    _VALID_URL = r'https?://(?:www\.)?ivi\.ru/watch/(?!\d+)(?P<compilationid>[a-z\d_-]+)(?:/season(?P<seasonid>\d+))?$'
    _TESTS = [{
        'url': 'http://www.ivi.ru/watch/dvoe_iz_lartsa',
        'info_dict': {
            'id': 'dvoe_iz_lartsa',
            'title': 'Двое из ларца (2006 - 2008)',
        },
        'playlist_mincount': 24,
    }, {
        'url': 'http://www.ivi.ru/watch/dvoe_iz_lartsa/season1',
        'info_dict': {
            'id': 'dvoe_iz_lartsa/season1',
            'title': 'Двое из ларца (2006 - 2008) 1 сезон',
        },
        'playlist_mincount': 12,
    }]

    def _extract_entries(self, html, compilation_id):
        return [self.url_result('http://www.ivi.ru/watch/%s/%s' % (compilation_id, serie), 'Ivi')
                for serie in re.findall(r'<strong><a href="/watch/%s/(\d+)">(?:[^<]+)</a></strong>' % compilation_id, html)]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        compilation_id = mobj.group('compilationid')
        season_id = mobj.group('seasonid')

        if season_id is not None:  # Season link
            season_page = self._download_webpage(url, compilation_id, 'Downloading season %s web page' % season_id)
            playlist_id = '%s/season%s' % (compilation_id, season_id)
            playlist_title = self._html_search_meta('title', season_page, 'title')
            entries = self._extract_entries(season_page, compilation_id)
        else:  # Compilation link
            compilation_page = self._download_webpage(url, compilation_id, 'Downloading compilation web page')
            playlist_id = compilation_id
            playlist_title = self._html_search_meta('title', compilation_page, 'title')
            seasons = re.findall(r'<a href="/watch/%s/season(\d+)">[^<]+</a>' % compilation_id, compilation_page)
            if len(seasons) == 0:  # No seasons in this compilation
                entries = self._extract_entries(compilation_page, compilation_id)
            else:
                entries = []
                for season_id in seasons:
                    season_page = self._download_webpage(
                        'http://www.ivi.ru/watch/%s/season%s' % (compilation_id, season_id),
                        compilation_id, 'Downloading season %s web page' % season_id)
                    entries.extend(self._extract_entries(season_page, compilation_id))

        return self.playlist_result(entries, playlist_id, playlist_title)
