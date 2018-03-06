# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    parse_duration,
    update_url_query,
)


class TVNowBaseIE(InfoExtractor):
    _VIDEO_FIELDS = (
        'id', 'title', 'free', 'geoblocked', 'articleLong', 'articleShort',
        'broadcastStartDate', 'isDrm', 'duration', 'season', 'episode',
        'manifest.dashclear', 'format.title', 'format.defaultImage169Format',
        'format.defaultImage169Logo')

    def _call_api(self, path, video_id, query):
        return self._download_json(
            'https://api.tvnow.de/v3/' + path,
            video_id, query=query)

    def _extract_video(self, info, display_id):
        video_id = compat_str(info['id'])
        title = info['title']

        mpd_url = info['manifest']['dashclear']
        if not mpd_url:
            if info.get('isDrm'):
                raise ExtractorError(
                    'Video %s is DRM protected' % video_id, expected=True)
            if info.get('geoblocked'):
                raise ExtractorError(
                    'Video %s is not available from your location due to geo restriction' % video_id,
                    expected=True)
            if not info.get('free', True):
                raise ExtractorError(
                    'Video %s is not available for free' % video_id, expected=True)

        mpd_url = update_url_query(mpd_url, {'filter': ''})
        formats = self._extract_mpd_formats(mpd_url, video_id, mpd_id='dash', fatal=False)
        formats.extend(self._extract_ism_formats(
            mpd_url.replace('dash.', 'hss.').replace('/.mpd', '/Manifest'),
            video_id, ism_id='mss', fatal=False))
        formats.extend(self._extract_m3u8_formats(
            mpd_url.replace('dash.', 'hls.').replace('/.mpd', '/.m3u8'),
            video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))
        self._sort_formats(formats)

        description = info.get('articleLong') or info.get('articleShort')
        timestamp = parse_iso8601(info.get('broadcastStartDate'), ' ')
        duration = parse_duration(info.get('duration'))

        f = info.get('format', {})
        thumbnail = f.get('defaultImage169Format') or f.get('defaultImage169Logo')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'series': f.get('title'),
            'season_number': int_or_none(info.get('season')),
            'episode_number': int_or_none(info.get('episode')),
            'episode': title,
            'formats': formats,
        }


class TVNowIE(TVNowBaseIE):
    _VALID_URL = r'https?://(?:www\.)?tvnow\.(?:de|at|ch)/(?:rtl(?:2|plus)?|nitro|superrtl|ntv|vox)/(?P<show_id>[^/]+)/(?:(?:list/[^/]+|jahr/\d{4}/\d{1,2})/)?(?P<id>[^/]+)/(?:player|preview)'

    _TESTS = [{
        'url': 'https://www.tvnow.de/rtl2/grip-das-motormagazin/der-neue-porsche-911-gt-3/player',
        'info_dict': {
            'id': '331082',
            'display_id': 'grip-das-motormagazin/der-neue-porsche-911-gt-3',
            'ext': 'mp4',
            'title': 'Der neue Porsche 911 GT 3',
            'description': 'md5:6143220c661f9b0aae73b245e5d898bb',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1495994400,
            'upload_date': '20170528',
            'duration': 5283,
            'series': 'GRIP - Das Motormagazin',
            'season_number': 14,
            'episode_number': 405,
            'episode': 'Der neue Porsche 911 GT 3',
        },
    }, {
        # rtl2
        'url': 'https://www.tvnow.de/rtl2/armes-deutschland/episode-0008/player',
        'only_matching': 'True',
    }, {
        # rtlnitro
        'url': 'https://www.tvnow.de/nitro/alarm-fuer-cobra-11-die-autobahnpolizei/auf-eigene-faust-pilot/player',
        'only_matching': 'True',
    }, {
        # superrtl
        'url': 'https://www.tvnow.de/superrtl/die-lustigsten-schlamassel-der-welt/u-a-ketchup-effekt/player',
        'only_matching': 'True',
    }, {
        # ntv
        'url': 'https://www.tvnow.de/ntv/startup-news/goetter-in-weiss/player',
        'only_matching': 'True',
    }, {
        # vox
        'url': 'https://www.tvnow.de/vox/auto-mobil/neues-vom-automobilmarkt-2017-11-19-17-00-00/player',
        'only_matching': 'True',
    }, {
        # rtlplus
        'url': 'https://www.tvnow.de/rtlplus/op-ruft-dr-bruckner/die-vernaehte-frau/player',
        'only_matching': 'True',
    }]

    def _real_extract(self, url):
        display_id = '%s/%s' % re.match(self._VALID_URL, url).groups()

        info = self._call_api(
            'movies/' + display_id, display_id, query={
                'fields': ','.join(self._VIDEO_FIELDS),
            })

        return self._extract_video(info, display_id)


class TVNowListIE(TVNowBaseIE):
    _VALID_URL = r'(?P<base_url>https?://(?:www\.)?tvnow\.(?:de|at|ch)/(?:rtl(?:2|plus)?|nitro|superrtl|ntv|vox)/(?P<show_id>[^/]+)/)list/(?P<id>[^?/#&]+)$'

    _SHOW_FIELDS = ('title', )
    _SEASON_FIELDS = ('id', 'headline', 'seoheadline', )
    _VIDEO_FIELDS = ('id', 'headline', 'seoUrl', )

    _TESTS = [{
        'url': 'https://www.tvnow.de/rtl/30-minuten-deutschland/list/aktuell',
        'info_dict': {
            'id': '28296',
            'title': '30 Minuten Deutschland - Aktuell',
        },
        'playlist_mincount': 1,
    }]

    def _real_extract(self, url):
        base_url, show_id, season_id = re.match(self._VALID_URL, url).groups()

        fields = []
        fields.extend(self._SHOW_FIELDS)
        fields.extend('formatTabs.%s' % field for field in self._SEASON_FIELDS)
        fields.extend(
            'formatTabs.formatTabPages.container.movies.%s' % field
            for field in self._VIDEO_FIELDS)

        list_info = self._call_api(
            'formats/seo', season_id, query={
                'fields': ','.join(fields),
                'name': show_id + '.php'
            })

        season = next(
            season for season in list_info['formatTabs']['items']
            if season.get('seoheadline') == season_id)

        title = '%s - %s' % (list_info['title'], season['headline'])

        entries = []
        for container in season['formatTabPages']['items']:
            for info in ((container.get('container') or {}).get('movies') or {}).get('items') or []:
                seo_url = info.get('seoUrl')
                if not seo_url:
                    continue
                entries.append(self.url_result(
                    base_url + seo_url + '/player', 'TVNow', info.get('id')))

        return self.playlist_result(
            entries, compat_str(season.get('id') or season_id), title)
