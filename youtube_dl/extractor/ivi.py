# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    qualities,
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
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'skip': 'Only works from Russia',
        },
        # Serial's series
        {
            'url': 'http://www.ivi.ru/watch/dvoe_iz_lartsa/9549',
            'md5': '221f56b35e3ed815fde2df71032f4b3e',
            'info_dict': {
                'id': '9549',
                'ext': 'mp4',
                'title': 'Двое из ларца - Дело Гольдберга (1 часть)',
                'series': 'Двое из ларца',
                'season': 'Сезон 1',
                'season_number': 1,
                'episode': 'Дело Гольдберга (1 часть)',
                'episode_number': 1,
                'duration': 2655,
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'skip': 'Only works from Russia',
        },
        {
            # with MP4-HD720 format
            'url': 'http://www.ivi.ru/watch/146500',
            'md5': 'd63d35cdbfa1ea61a5eafec7cc523e1e',
            'info_dict': {
                'id': '146500',
                'ext': 'mp4',
                'title': 'Кукла',
                'description': 'md5:ffca9372399976a2d260a407cc74cce6',
                'duration': 5599,
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'skip': 'Only works from Russia',
        }
    ]

    # Sorted by quality
    _KNOWN_FORMATS = (
        'MP4-low-mobile', 'MP4-mobile', 'FLV-lo', 'MP4-lo', 'FLV-hi', 'MP4-hi',
        'MP4-SHQ', 'MP4-HD720', 'MP4-HD1080')

    def _real_extract(self, url):
        video_id = self._match_id(url)

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

        video_json = self._download_json(
            'http://api.digitalaccess.ru/api/json/', video_id,
            'Downloading video JSON', data=json.dumps(data))

        if 'error' in video_json:
            error = video_json['error']
            if error['origin'] == 'NoRedisValidData':
                raise ExtractorError('Video %s does not exist' % video_id, expected=True)
            raise ExtractorError(
                'Unable to download video %s: %s' % (video_id, error['message']),
                expected=True)

        result = video_json['result']

        quality = qualities(self._KNOWN_FORMATS)

        formats = [{
            'url': x['url'],
            'format_id': x.get('content_format'),
            'quality': quality(x.get('content_format')),
        } for x in result['files'] if x.get('url')]

        self._sort_formats(formats)

        title = result['title']

        duration = int_or_none(result.get('duration'))
        compilation = result.get('compilation')
        episode = title if compilation else None

        title = '%s - %s' % (compilation, title) if compilation is not None else title

        thumbnails = [{
            'url': preview['url'],
            'id': preview.get('content_format'),
        } for preview in result.get('preview', []) if preview.get('url')]

        webpage = self._download_webpage(url, video_id)

        season = self._search_regex(
            r'<li[^>]+class="season active"[^>]*><a[^>]+>([^<]+)',
            webpage, 'season', default=None)
        season_number = int_or_none(self._search_regex(
            r'<li[^>]+class="season active"[^>]*><a[^>]+data-season(?:-index)?="(\d+)"',
            webpage, 'season number', default=None))

        episode_number = int_or_none(self._search_regex(
            r'[^>]+itemprop="episode"[^>]*>\s*<meta[^>]+itemprop="episodeNumber"[^>]+content="(\d+)',
            webpage, 'episode number', default=None))

        description = self._og_search_description(webpage, default=None) or self._html_search_meta(
            'description', webpage, 'description', default=None)

        return {
            'id': video_id,
            'title': title,
            'series': compilation,
            'season': season,
            'season_number': season_number,
            'episode': episode,
            'episode_number': episode_number,
            'thumbnails': thumbnails,
            'description': description,
            'duration': duration,
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
        return [
            self.url_result(
                'http://www.ivi.ru/watch/%s/%s' % (compilation_id, serie), IviIE.ie_key())
            for serie in re.findall(
                r'<a href="/watch/%s/(\d+)"[^>]+data-id="\1"' % compilation_id, html)]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        compilation_id = mobj.group('compilationid')
        season_id = mobj.group('seasonid')

        if season_id is not None:  # Season link
            season_page = self._download_webpage(
                url, compilation_id, 'Downloading season %s web page' % season_id)
            playlist_id = '%s/season%s' % (compilation_id, season_id)
            playlist_title = self._html_search_meta('title', season_page, 'title')
            entries = self._extract_entries(season_page, compilation_id)
        else:  # Compilation link
            compilation_page = self._download_webpage(url, compilation_id, 'Downloading compilation web page')
            playlist_id = compilation_id
            playlist_title = self._html_search_meta('title', compilation_page, 'title')
            seasons = re.findall(
                r'<a href="/watch/%s/season(\d+)' % compilation_id, compilation_page)
            if not seasons:  # No seasons in this compilation
                entries = self._extract_entries(compilation_page, compilation_id)
            else:
                entries = []
                for season_id in seasons:
                    season_page = self._download_webpage(
                        'http://www.ivi.ru/watch/%s/season%s' % (compilation_id, season_id),
                        compilation_id, 'Downloading season %s web page' % season_id)
                    entries.extend(self._extract_entries(season_page, compilation_id))

        return self.playlist_result(entries, playlist_id, playlist_title)
