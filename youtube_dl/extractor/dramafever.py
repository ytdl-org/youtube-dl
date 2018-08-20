# coding: utf-8
from __future__ import unicode_literals

import itertools
import json

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_urlparse,
)
from ..utils import (
    clean_html,
    ExtractorError,
    int_or_none,
    parse_age_limit,
    parse_duration,
    unified_timestamp,
    url_or_none,
)


class DramaFeverBaseIE(InfoExtractor):
    _NETRC_MACHINE = 'dramafever'

    _CONSUMER_SECRET = 'DA59dtVXYLxajktV'

    _consumer_secret = None

    def _get_consumer_secret(self):
        mainjs = self._download_webpage(
            'http://www.dramafever.com/static/51afe95/df2014/scripts/main.js',
            None, 'Downloading main.js', fatal=False)
        if not mainjs:
            return self._CONSUMER_SECRET
        return self._search_regex(
            r"var\s+cs\s*=\s*'([^']+)'", mainjs,
            'consumer secret', default=self._CONSUMER_SECRET)

    def _real_initialize(self):
        self._consumer_secret = self._get_consumer_secret()
        self._login()

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        login_form = {
            'username': username,
            'password': password,
        }

        try:
            response = self._download_json(
                'https://www.dramafever.com/api/users/login', None, 'Logging in',
                data=json.dumps(login_form).encode('utf-8'), headers={
                    'x-consumer-key': self._consumer_secret,
                })
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code in (403, 404):
                response = self._parse_json(
                    e.cause.read().decode('utf-8'), None)
            else:
                raise

        # Successful login
        if response.get('result') or response.get('guid') or response.get('user_guid'):
            return

        errors = response.get('errors')
        if errors and isinstance(errors, list):
            error = errors[0]
            message = error.get('message') or error['reason']
            raise ExtractorError('Unable to login: %s' % message, expected=True)
        raise ExtractorError('Unable to log in')


class DramaFeverIE(DramaFeverBaseIE):
    IE_NAME = 'dramafever'
    _VALID_URL = r'https?://(?:www\.)?dramafever\.com/(?:[^/]+/)?drama/(?P<id>[0-9]+/[0-9]+)(?:/|$)'
    _TESTS = [{
        'url': 'https://www.dramafever.com/drama/4274/1/Heirs/',
        'info_dict': {
            'id': '4274.1',
            'ext': 'wvm',
            'title': 'Heirs - Episode 1',
            'description': 'md5:362a24ba18209f6276e032a651c50bc2',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 3783,
            'timestamp': 1381354993,
            'upload_date': '20131009',
            'series': 'Heirs',
            'season_number': 1,
            'episode': 'Episode 1',
            'episode_number': 1,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://www.dramafever.com/drama/4826/4/Mnet_Asian_Music_Awards_2015/?ap=1',
        'info_dict': {
            'id': '4826.4',
            'ext': 'flv',
            'title': 'Mnet Asian Music Awards 2015',
            'description': 'md5:3ff2ee8fedaef86e076791c909cf2e91',
            'episode': 'Mnet Asian Music Awards 2015 - Part 3',
            'episode_number': 4,
            'thumbnail': r're:^https?://.*\.jpg',
            'timestamp': 1450213200,
            'upload_date': '20151215',
            'duration': 5359,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'https://www.dramafever.com/zh-cn/drama/4972/15/Doctor_Romantic/',
        'only_matching': True,
    }]

    def _call_api(self, path, video_id, note, fatal=False):
        return self._download_json(
            'https://www.dramafever.com/api/5/' + path,
            video_id, note=note, headers={
                'x-consumer-key': self._consumer_secret,
            }, fatal=fatal)

    def _get_subtitles(self, video_id):
        subtitles = {}
        subs = self._call_api(
            'video/%s/subtitles/webvtt/' % video_id, video_id,
            'Downloading subtitles JSON', fatal=False)
        if not subs or not isinstance(subs, list):
            return subtitles
        for sub in subs:
            if not isinstance(sub, dict):
                continue
            sub_url = url_or_none(sub.get('url'))
            if not sub_url:
                continue
            subtitles.setdefault(
                sub.get('code') or sub.get('language') or 'en', []).append({
                    'url': sub_url
                })
        return subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url).replace('/', '.')

        series_id, episode_number = video_id.split('.')

        video = self._call_api(
            'series/%s/episodes/%s/' % (series_id, episode_number), video_id,
            'Downloading video JSON')

        formats = []
        download_assets = video.get('download_assets')
        if download_assets and isinstance(download_assets, dict):
            for format_id, format_dict in download_assets.items():
                if not isinstance(format_dict, dict):
                    continue
                format_url = url_or_none(format_dict.get('url'))
                if not format_url:
                    continue
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                    'filesize': int_or_none(video.get('filesize')),
                })

        stream = self._call_api(
            'video/%s/stream/' % video_id, video_id, 'Downloading stream JSON',
            fatal=False)
        if stream:
            stream_url = stream.get('stream_url')
            if stream_url:
                formats.extend(self._extract_m3u8_formats(
                    stream_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
        self._sort_formats(formats)

        title = video.get('title') or 'Episode %s' % episode_number
        description = video.get('description')
        thumbnail = video.get('thumbnail')
        timestamp = unified_timestamp(video.get('release_date'))
        duration = parse_duration(video.get('duration'))
        age_limit = parse_age_limit(video.get('tv_rating'))
        series = video.get('series_title')
        season_number = int_or_none(video.get('season'))

        if series:
            title = '%s - %s' % (series, title)

        subtitles = self.extract_subtitles(video_id)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'timestamp': timestamp,
            'age_limit': age_limit,
            'series': series,
            'season_number': season_number,
            'episode_number': int_or_none(episode_number),
            'formats': formats,
            'subtitles': subtitles,
        }


class DramaFeverSeriesIE(DramaFeverBaseIE):
    IE_NAME = 'dramafever:series'
    _VALID_URL = r'https?://(?:www\.)?dramafever\.com/(?:[^/]+/)?drama/(?P<id>[0-9]+)(?:/(?:(?!\d+(?:/|$)).+)?)?$'
    _TESTS = [{
        'url': 'http://www.dramafever.com/drama/4512/Cooking_with_Shin/',
        'info_dict': {
            'id': '4512',
            'title': 'Cooking with Shin',
            'description': 'md5:84a3f26e3cdc3fb7f500211b3593b5c1',
        },
        'playlist_count': 4,
    }, {
        'url': 'http://www.dramafever.com/drama/124/IRIS/',
        'info_dict': {
            'id': '124',
            'title': 'IRIS',
            'description': 'md5:b3a30e587cf20c59bd1c01ec0ee1b862',
        },
        'playlist_count': 20,
    }]

    _PAGE_SIZE = 60  # max is 60 (see http://api.drama9.com/#get--api-4-episode-series-)

    def _real_extract(self, url):
        series_id = self._match_id(url)

        series = self._download_json(
            'http://www.dramafever.com/api/4/series/query/?cs=%s&series_id=%s'
            % (self._consumer_secret, series_id),
            series_id, 'Downloading series JSON')['series'][series_id]

        title = clean_html(series['name'])
        description = clean_html(series.get('description') or series.get('description_short'))

        entries = []
        for page_num in itertools.count(1):
            episodes = self._download_json(
                'http://www.dramafever.com/api/4/episode/series/?cs=%s&series_id=%s&page_size=%d&page_number=%d'
                % (self._consumer_secret, series_id, self._PAGE_SIZE, page_num),
                series_id, 'Downloading episodes JSON page #%d' % page_num)
            for episode in episodes.get('value', []):
                episode_url = episode.get('episode_url')
                if not episode_url:
                    continue
                entries.append(self.url_result(
                    compat_urlparse.urljoin(url, episode_url),
                    'DramaFever', episode.get('guid')))
            if page_num == episodes['num_pages']:
                break

        return self.playlist_result(entries, series_id, title, description)
