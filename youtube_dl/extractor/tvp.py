# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class TvpIE(InfoExtractor):
    IE_NAME = 'tvp.pl'
    _VALID_URL = r'https?://(?:vod|www)\.tvp\.pl/.*/(?P<id>\d+)$'

    _TESTS = [{
        'url': 'http://vod.tvp.pl/filmy-fabularne/filmy-za-darmo/ogniem-i-mieczem/wideo/odc-2/4278035',
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
        'md5': 'c3b15ed1af288131115ff17a17c19dda',
        'info_dict': {
            'id': '17916176',
            'ext': 'mp4',
            'title': 'TVP Gorzów pokaże filmy studentów z podroży dookoła świata',
        },
    }, {
        'url': 'http://vod.tvp.pl/seriale/obyczajowe/na-sygnale/sezon-2-27-/odc-39/17834272',
        'md5': 'c3b15ed1af288131115ff17a17c19dda',
        'info_dict': {
            'id': '17834272',
            'ext': 'mp4',
            'title': 'Na sygnale, odc. 39',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

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

        video_url = self._search_regex(
            r'0:{src:([\'"])(?P<url>.*?)\1', webpage, 'formats', group='url', default=None)
        if not video_url:
            video_url = self._download_json(
                'http://www.tvp.pl/pub/stat/videofileinfo?video_id=%s' % video_id,
                video_id)['video_url']

        ext = video_url.rsplit('.', 1)[-1]
        if ext != 'ism/manifest':
            if '/' in ext:
                ext = 'mp4'
            formats = [{
                'format_id': 'direct',
                'url': video_url,
                'ext': ext,
            }]
        else:
            m3u8_url = re.sub('([^/]*)\.ism/manifest', r'\1.ism/\1.m3u8', video_url)
            formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4')

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }


class TvpSeriesIE(InfoExtractor):
    IE_NAME = 'tvp.pl:Series'
    _VALID_URL = r'https?://vod\.tvp\.pl/(?:[^/]+/){2}(?P<id>[^/]+)/?$'

    _TESTS = [{
        'url': 'http://vod.tvp.pl/filmy-fabularne/filmy-za-darmo/ogniem-i-mieczem',
        'info_dict': {
            'title': 'Ogniem i mieczem',
            'id': '4278026',
        },
        'playlist_count': 4,
    }, {
        'url': 'http://vod.tvp.pl/audycje/podroze/boso-przez-swiat',
        'info_dict': {
            'title': 'Boso przez świat',
            'id': '9329207',
        },
        'playlist_count': 86,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id, tries=5)

        title = self._html_search_regex(
            r'(?s) id=[\'"]path[\'"]>(?:.*? / ){2}(.*?)</span>', webpage, 'series')
        playlist_id = self._search_regex(r'nodeId:\s*(\d+)', webpage, 'playlist id')
        playlist = self._download_webpage(
            'http://vod.tvp.pl/vod/seriesAjax?type=series&nodeId=%s&recommend'
            'edId=0&sort=&page=0&pageSize=10000' % playlist_id, display_id, tries=5,
            note='Downloading playlist')

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
