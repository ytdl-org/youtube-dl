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
    try_get,
    update_url_query,
)


class TVNowBaseIE(InfoExtractor):
    _VIDEO_FIELDS = (
        'id', 'title', 'free', 'geoblocked', 'articleLong', 'articleShort',
        'broadcastStartDate', 'isDrm', 'duration', 'season', 'episode',
        'manifest.dashclear', 'manifest.hlsclear', 'manifest.smoothclear',
        'format.title', 'format.defaultImage169Format', 'format.defaultImage169Logo')

    def _call_api(self, path, video_id, query):
        return self._download_json(
            'https://api.tvnow.de/v3/' + path,
            video_id, query=query)

    def _extract_video(self, info, display_id):
        video_id = compat_str(info['id'])
        title = info['title']

        paths = []
        for manifest_url in (info.get('manifest') or {}).values():
            if not manifest_url:
                continue
            manifest_url = update_url_query(manifest_url, {'filter': ''})
            path = self._search_regex(r'https?://[^/]+/(.+?)\.ism/', manifest_url, 'path')
            if path in paths:
                continue
            paths.append(path)

            def url_repl(proto, suffix):
                return re.sub(
                    r'(?:hls|dash|hss)([.-])', proto + r'\1', re.sub(
                        r'\.ism/(?:[^.]*\.(?:m3u8|mpd)|[Mm]anifest)',
                        '.ism/' + suffix, manifest_url))

            formats = self._extract_mpd_formats(
                url_repl('dash', '.mpd'), video_id,
                mpd_id='dash', fatal=False)
            formats.extend(self._extract_ism_formats(
                url_repl('hss', 'Manifest'),
                video_id, ism_id='mss', fatal=False))
            formats.extend(self._extract_m3u8_formats(
                url_repl('hls', '.m3u8'), video_id, 'mp4',
                'm3u8_native', m3u8_id='hls', fatal=False))
            if formats:
                break
        else:
            if info.get('isDrm'):
                raise ExtractorError(
                    'Video %s is DRM protected' % video_id, expected=True)
            if info.get('geoblocked'):
                raise self.raise_geo_restricted()
            if not info.get('free', True):
                raise ExtractorError(
                    'Video %s is not available for free' % video_id, expected=True)
        self._sort_formats(formats)

        description = info.get('articleLong') or info.get('articleShort')
        timestamp = parse_iso8601(info.get('broadcastStartDate'), ' ')
        duration = parse_duration(info.get('duration'))

        f = info.get('format', {})

        thumbnails = [{
            'url': 'https://aistvnow-a.akamaihd.net/tvnow/movie/%s' % video_id,
        }]
        thumbnail = f.get('defaultImage169Format') or f.get('defaultImage169Logo')
        if thumbnail:
            thumbnails.append({
                'url': thumbnail,
            })

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'timestamp': timestamp,
            'duration': duration,
            'series': f.get('title'),
            'season_number': int_or_none(info.get('season')),
            'episode_number': int_or_none(info.get('episode')),
            'episode': title,
            'formats': formats,
        }


class TVNowIE(TVNowBaseIE):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.)?tvnow\.(?:de|at|ch)/(?P<station>[^/]+)/
                        (?P<show_id>[^/]+)/
                        (?!(?:list|jahr)(?:/|$))(?P<id>[^/?\#&]+)
                    '''

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
        'only_matching': True,
    }, {
        # rtlnitro
        'url': 'https://www.tvnow.de/nitro/alarm-fuer-cobra-11-die-autobahnpolizei/auf-eigene-faust-pilot/player',
        'only_matching': True,
    }, {
        # superrtl
        'url': 'https://www.tvnow.de/superrtl/die-lustigsten-schlamassel-der-welt/u-a-ketchup-effekt/player',
        'only_matching': True,
    }, {
        # ntv
        'url': 'https://www.tvnow.de/ntv/startup-news/goetter-in-weiss/player',
        'only_matching': True,
    }, {
        # vox
        'url': 'https://www.tvnow.de/vox/auto-mobil/neues-vom-automobilmarkt-2017-11-19-17-00-00/player',
        'only_matching': True,
    }, {
        # rtlplus
        'url': 'https://www.tvnow.de/rtlplus/op-ruft-dr-bruckner/die-vernaehte-frau/player',
        'only_matching': True,
    }, {
        'url': 'https://www.tvnow.de/rtl2/grip-das-motormagazin/der-neue-porsche-911-gt-3',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = '%s/%s' % mobj.group(2, 3)

        info = self._call_api(
            'movies/' + display_id, display_id, query={
                'fields': ','.join(self._VIDEO_FIELDS),
                'station': mobj.group(1),
            })

        return self._extract_video(info, display_id)


class TVNowListBaseIE(TVNowBaseIE):
    _SHOW_VALID_URL = r'''(?x)
                    (?P<base_url>
                        https?://
                            (?:www\.)?tvnow\.(?:de|at|ch)/[^/]+/
                            (?P<show_id>[^/]+)
                    )
                    '''

    def _extract_list_info(self, display_id, show_id):
        fields = list(self._SHOW_FIELDS)
        fields.extend('formatTabs.%s' % field for field in self._SEASON_FIELDS)
        fields.extend(
            'formatTabs.formatTabPages.container.movies.%s' % field
            for field in self._VIDEO_FIELDS)
        return self._call_api(
            'formats/seo', display_id, query={
                'fields': ','.join(fields),
                'name': show_id + '.php'
            })


class TVNowListIE(TVNowListBaseIE):
    _VALID_URL = r'%s/(?:list|jahr)/(?P<id>[^?\#&]+)' % TVNowListBaseIE._SHOW_VALID_URL

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
    }, {
        'url': 'https://www.tvnow.de/vox/ab-ins-beet/list/staffel-14',
        'only_matching': True,
    }, {
        'url': 'https://www.tvnow.de/rtl2/grip-das-motormagazin/jahr/2018/3',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return (False if TVNowIE.suitable(url)
                else super(TVNowListIE, cls).suitable(url))

    def _real_extract(self, url):
        base_url, show_id, season_id = re.match(self._VALID_URL, url).groups()

        list_info = self._extract_list_info(season_id, show_id)

        season = next(
            season for season in list_info['formatTabs']['items']
            if season.get('seoheadline') == season_id)

        title = list_info.get('title')
        headline = season.get('headline')
        if title and headline:
            title = '%s - %s' % (title, headline)
        else:
            title = headline or title

        entries = []
        for container in season['formatTabPages']['items']:
            items = try_get(
                container, lambda x: x['container']['movies']['items'],
                list) or []
            for info in items:
                seo_url = info.get('seoUrl')
                if not seo_url:
                    continue
                video_id = info.get('id')
                entries.append(self.url_result(
                    '%s/%s/player' % (base_url, seo_url), TVNowIE.ie_key(),
                    compat_str(video_id) if video_id else None))

        return self.playlist_result(
            entries, compat_str(season.get('id') or season_id), title)


class TVNowShowIE(TVNowListBaseIE):
    _VALID_URL = TVNowListBaseIE._SHOW_VALID_URL

    _SHOW_FIELDS = ('id', 'title', )
    _SEASON_FIELDS = ('id', 'headline', 'seoheadline', )
    _VIDEO_FIELDS = ()

    _TESTS = [{
        'url': 'https://www.tvnow.at/vox/ab-ins-beet',
        'info_dict': {
            'id': 'ab-ins-beet',
            'title': 'Ab ins Beet!',
        },
        'playlist_mincount': 7,
    }, {
        'url': 'https://www.tvnow.at/vox/ab-ins-beet/list',
        'only_matching': True,
    }, {
        'url': 'https://www.tvnow.de/rtl2/grip-das-motormagazin/jahr/',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return (False if TVNowIE.suitable(url) or TVNowListIE.suitable(url)
                else super(TVNowShowIE, cls).suitable(url))

    def _real_extract(self, url):
        base_url, show_id = re.match(self._VALID_URL, url).groups()

        list_info = self._extract_list_info(show_id, show_id)

        entries = []
        for season_info in list_info['formatTabs']['items']:
            season_url = season_info.get('seoheadline')
            if not season_url:
                continue
            season_id = season_info.get('id')
            entries.append(self.url_result(
                '%s/list/%s' % (base_url, season_url), TVNowListIE.ie_key(),
                compat_str(season_id) if season_id else None,
                season_info.get('headline')))

        return self.playlist_result(entries, show_id, list_info.get('title'))
