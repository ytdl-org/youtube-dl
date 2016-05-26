# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class TvpIE(InfoExtractor):
    IE_NAME = 'tvp.pl'
    _VALID_URL = r'https?://(?:vod|www)\.tvp\.pl.*?/(?P<id>\d+).*?$'

    _TESTS = [{
        'url': 'http://vod.tvp.pl/4278035/odc-2',
        'md5': 'cdd98303338b8a7f7abab5cd14092bf2',
        'info_dict': {
            'id': '4278035',
            'ext': 'wmv',
            'title': 'Ogniem i mieczem, odc. 2',
        },
    }, {
        'url': 'http://vod.tvp.pl/seriale/obyczajowe/czas-honoru/sezon-1-1-13/i-seria-odc-13/194536',
        'md5': '8aa518c15e5cc32dfe8db400dc921fbb',
        'info_dict': {
            'id': '194536',
            'ext': 'mp4',
            'title': 'Czas honoru, I seria – odc. 13',
        },
    }, {
        'url': 'http://www.tvp.pl/there-can-be-anything-so-i-shortened-it/17916176',
        'md5': 'b95f1f14afb419103e7af378fb706d61',
        'info_dict': {
            'id': '17916176',
            'ext': 'mp4',
            'title': 'TVP Gorzów pokaże filmy studentów z podroży dookoła świata',
        },
    }, {
        'url': 'http://vod.tvp.pl/seriale/obyczajowe/na-sygnale/sezon-2-27-/odc-39/17834272',
        'md5': 'd2a61fd2fbe3a8865f992af244e2f1b5',
        'info_dict': {
            'id': '17834272',
            'ext': 'mp4',
            'title': 'Na sygnale, odc. 39',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if "player" not in webpage:
            return self.url_result(url, ie=TvpSeriesIE.ie_key())

        webpage = self._download_webpage(
            'http://www.tvp.pl/sess/tvplayer.php?object_id=%s' % video_id, video_id)

        title = self._search_regex(
            r'name\s*:\s*([\'"])Title\1\s*,\s*value\s*:\s*\1(?P<title>.+?)\1',
            webpage, 'title', group='title')
        series_title = self._search_regex(
            r'name\s*:\s*([\'"])SeriesTitle\1\s*,\s*value\s*:\s*\1(?P<series>.+?)\1',
            webpage, 'series', group='series', default=None)
        if series_title:
            title = '%s, %s' % (series_title, title)

        thumbnail = self._search_regex(
            r"poster\s*:\s*'([^']+)'", webpage, 'thumbnail', default=None)

        formats = []
        matches = re.finditer(r'\d+:{src:([\'"])(?P<url>.*?)\1', webpage)
        for m in matches:
            formats += self._prepare_format(m.group('url'), video_id)
        if not formats:
            video_url = self._download_json(
                'http://www.tvp.pl/pub/stat/videofileinfo?video_id=%s' % video_id, video_id)['video_url']
            formats += self._prepare_format(video_url, video_id, lq=True)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }

    def _prepare_format(self, video_url, video_id, lq=False):
        ext = video_url.rsplit('.', 1)[-1]
        if ext != 'ism/manifest':
            if '/' in ext:
                ext = 'mp4'
            return [{
                'format_id': 'direct' + ('_lq' if lq else ''),
                'url': video_url,
                'ext': ext,
            }]
        else:
            m3u8_url = re.sub('([^/]*)\.ism/manifest', r'\1.ism/\1.m3u8', video_url)
            return self._extract_m3u8_formats(m3u8_url, video_id, 'mp4')


class TvpSeriesIE(InfoExtractor):
    IE_NAME = 'tvp.pl:Series'
    _VALID_URL = r'https?://vod\.tvp\.pl/(?P<id>[^/]+)/.*$'

    _TESTS = [{
        'url': 'http://vod.tvp.pl/4278026/ogniem-i-mieczem',
        'info_dict': {
            'title': 'Ogniem i mieczem',
            'id': '4278026',
        },
        'playlist_count': 4,
    }, {
        'url': 'http://vod.tvp.pl/9329207/boso-przez-swiat',
        'info_dict': {
            'title': 'Boso przez świat',
            'id': '9329207',
        },
        'playlist_count': 86,
    }]

    def _real_extract(self, url):
        display_id = url.split("/")[-1]
        webpage = self._download_webpage(url, display_id)

        if "player" in webpage:
            return self.url_result(url, ie=TvpIE.ie_key())

        title = self._og_search_title(webpage)
        playlist_id = self._match_id(url)
        playlist = self._download_webpage(
            'http://vod.tvp.pl/shared/listing.php?page=1&count=1000&type=video&direct=false'
            '&filter=%%7B%%22playable%%22%%3Atrue%%7D&template=directory/listing.html'
            '&parent_id=%s' % playlist_id, display_id, note='Downloading playlist')

        videos_paths = re.findall(
            '(?s)class="shortTitle">.*?href="(/[^"]+)', playlist)
        entries = [
            self.url_result('http://vod.tvp.pl%s' % v_path, ie=TvpIE.ie_key())
            for v_path in videos_paths]

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'display_id': display_id,
            'title': title,
            'entries': entries,
        }
