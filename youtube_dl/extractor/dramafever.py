# encoding: utf-8
from __future__ import unicode_literals

import itertools

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    int_or_none,
    parse_iso8601,
)


class DramaFeverIE(InfoExtractor):
    IE_NAME = 'dramafever'
    _VALID_URL = r'https?://(?:www\.)?dramafever\.com/drama/(?P<id>[0-9]+/[0-9]+)(?:/|$)'
    _TEST = {
        'url': 'http://www.dramafever.com/drama/4512/1/Cooking_with_Shin/',
        'info_dict': {
            'id': '4512.1',
            'ext': 'flv',
            'title': 'Cooking with Shin 4512.1',
            'description': 'md5:a8eec7942e1664a6896fcd5e1287bfd0',
            'thumbnail': 're:^https?://.*\.jpg',
            'timestamp': 1404336058,
            'upload_date': '20140702',
            'duration': 343,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url).replace('/', '.')

        try:
            feed = self._download_json(
                'http://www.dramafever.com/amp/episode/feed.json?guid=%s' % video_id,
                video_id, 'Downloading episode JSON')['channel']['item']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError):
                raise ExtractorError(
                    'Currently unavailable in your country.', expected=True)
            raise

        media_group = feed.get('media-group', {})

        formats = []
        for media_content in media_group['media-content']:
            src = media_content.get('@attributes', {}).get('url')
            if not src:
                continue
            ext = determine_ext(src)
            if ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    src, video_id, f4m_id='hds'))
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    src, video_id, 'mp4', m3u8_id='hls'))
            else:
                formats.append({
                    'url': src,
                })
        self._sort_formats(formats)

        title = media_group.get('media-title')
        description = media_group.get('media-description')
        duration = int_or_none(media_group['media-content'][0].get('@attributes', {}).get('duration'))
        thumbnail = self._proto_relative_url(
            media_group.get('media-thumbnail', {}).get('@attributes', {}).get('url'))
        timestamp = parse_iso8601(feed.get('pubDate'), ' ')

        subtitles = {}
        for media_subtitle in media_group.get('media-subTitle', []):
            lang = media_subtitle.get('@attributes', {}).get('lang')
            href = media_subtitle.get('@attributes', {}).get('href')
            if not lang or not href:
                continue
            subtitles[lang] = [{
                'ext': 'ttml',
                'url': href,
            }]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
        }


class DramaFeverSeriesIE(InfoExtractor):
    IE_NAME = 'dramafever:series'
    _VALID_URL = r'https?://(?:www\.)?dramafever\.com/drama/(?P<id>[0-9]+)(?:/(?:(?!\d+(?:/|$)).+)?)?$'
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

    _CONSUMER_SECRET = 'DA59dtVXYLxajktV'
    _PAGE_SIZE = 60  # max is 60 (see http://api.drama9.com/#get--api-4-episode-series-)

    def _get_consumer_secret(self, video_id):
        mainjs = self._download_webpage(
            'http://www.dramafever.com/static/51afe95/df2014/scripts/main.js',
            video_id, 'Downloading main.js', fatal=False)
        if not mainjs:
            return self._CONSUMER_SECRET
        return self._search_regex(
            r"var\s+cs\s*=\s*'([^']+)'", mainjs,
            'consumer secret', default=self._CONSUMER_SECRET)

    def _real_extract(self, url):
        series_id = self._match_id(url)

        consumer_secret = self._get_consumer_secret(series_id)

        series = self._download_json(
            'http://www.dramafever.com/api/4/series/query/?cs=%s&series_id=%s'
            % (consumer_secret, series_id),
            series_id, 'Downloading series JSON')['series'][series_id]

        title = clean_html(series['name'])
        description = clean_html(series.get('description') or series.get('description_short'))

        entries = []
        for page_num in itertools.count(1):
            episodes = self._download_json(
                'http://www.dramafever.com/api/4/episode/series/?cs=%s&series_id=%s&page_size=%d&page_number=%d'
                % (consumer_secret, series_id, self._PAGE_SIZE, page_num),
                series_id, 'Downloading episodes JSON page #%d' % page_num)
            for episode in episodes.get('value', []):
                entries.append(self.url_result(
                    compat_urlparse.urljoin(url, episode['episode_url']),
                    'DramaFever', episode.get('guid')))
            if page_num == episodes['num_pages']:
                break

        return self.playlist_result(entries, series_id, title, description)
