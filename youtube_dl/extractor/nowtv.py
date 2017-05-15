# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    parse_iso8601,
    parse_duration,
    remove_start,
)


class NowTVBaseIE(InfoExtractor):
    _VIDEO_FIELDS = (
        'id', 'title', 'free', 'geoblocked', 'articleLong', 'articleShort',
        'broadcastStartDate', 'seoUrl', 'duration', 'files',
        'format.defaultImage169Format', 'format.defaultImage169Logo')

    def _extract_video(self, info, display_id=None):
        video_id = compat_str(info['id'])

        files = info['files']
        if not files:
            if info.get('geoblocked', False):
                raise ExtractorError(
                    'Video %s is not available from your location due to geo restriction' % video_id,
                    expected=True)
            if not info.get('free', True):
                raise ExtractorError(
                    'Video %s is not available for free' % video_id, expected=True)

        formats = []
        for item in files['items']:
            if determine_ext(item['path']) != 'f4v':
                continue
            app, play_path = remove_start(item['path'], '/').split('/', 1)
            formats.append({
                'url': 'rtmpe://fms.rtl.de',
                'app': app,
                'play_path': 'mp4:%s' % play_path,
                'ext': 'flv',
                'page_url': 'http://rtlnow.rtl.de',
                'player_url': 'http://cdn.static-fra.de/now/vodplayer.swf',
                'tbr': int_or_none(item.get('bitrate')),
            })
        self._sort_formats(formats)

        title = info['title']
        description = info.get('articleLong') or info.get('articleShort')
        timestamp = parse_iso8601(info.get('broadcastStartDate'), ' ')
        duration = parse_duration(info.get('duration'))

        f = info.get('format', {})
        thumbnail = f.get('defaultImage169Format') or f.get('defaultImage169Logo')

        return {
            'id': video_id,
            'display_id': display_id or info.get('seoUrl'),
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }


class NowTVIE(NowTVBaseIE):
    _WORKING = False
    _VALID_URL = r'https?://(?:www\.)?nowtv\.(?:de|at|ch)/(?:rtl|rtl2|rtlnitro|superrtl|ntv|vox)/(?P<show_id>[^/]+)/(?:(?:list/[^/]+|jahr/\d{4}/\d{1,2})/)?(?P<id>[^/]+)/(?:player|preview)'

    _TESTS = [{
        # rtl
        'url': 'http://www.nowtv.de/rtl/bauer-sucht-frau/die-neuen-bauern-und-eine-hochzeit/player',
        'info_dict': {
            'id': '203519',
            'display_id': 'bauer-sucht-frau/die-neuen-bauern-und-eine-hochzeit',
            'ext': 'flv',
            'title': 'Inka Bause stellt die neuen Bauern vor',
            'description': 'md5:e234e1ed6d63cf06be5c070442612e7e',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1432580700,
            'upload_date': '20150525',
            'duration': 2786,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }, {
        # rtl2
        'url': 'http://www.nowtv.de/rtl2/berlin-tag-nacht/berlin-tag-nacht-folge-934/player',
        'info_dict': {
            'id': '203481',
            'display_id': 'berlin-tag-nacht/berlin-tag-nacht-folge-934',
            'ext': 'flv',
            'title': 'Berlin - Tag & Nacht (Folge 934)',
            'description': 'md5:c85e88c2e36c552dfe63433bc9506dd0',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1432666800,
            'upload_date': '20150526',
            'duration': 2641,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }, {
        # rtlnitro
        'url': 'http://www.nowtv.de/rtlnitro/alarm-fuer-cobra-11-die-autobahnpolizei/hals-und-beinbruch-2014-08-23-21-10-00/player',
        'info_dict': {
            'id': '165780',
            'display_id': 'alarm-fuer-cobra-11-die-autobahnpolizei/hals-und-beinbruch-2014-08-23-21-10-00',
            'ext': 'flv',
            'title': 'Hals- und Beinbruch',
            'description': 'md5:b50d248efffe244e6f56737f0911ca57',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1432415400,
            'upload_date': '20150523',
            'duration': 2742,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }, {
        # superrtl
        'url': 'http://www.nowtv.de/superrtl/medicopter-117/angst/player',
        'info_dict': {
            'id': '99205',
            'display_id': 'medicopter-117/angst',
            'ext': 'flv',
            'title': 'Angst!',
            'description': 'md5:30cbc4c0b73ec98bcd73c9f2a8c17c4e',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1222632900,
            'upload_date': '20080928',
            'duration': 3025,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }, {
        # ntv
        'url': 'http://www.nowtv.de/ntv/ratgeber-geld/thema-ua-der-erste-blick-die-apple-watch/player',
        'info_dict': {
            'id': '203521',
            'display_id': 'ratgeber-geld/thema-ua-der-erste-blick-die-apple-watch',
            'ext': 'flv',
            'title': 'Thema u.a.: Der erste Blick: Die Apple Watch',
            'description': 'md5:4312b6c9d839ffe7d8caf03865a531af',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1432751700,
            'upload_date': '20150527',
            'duration': 1083,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }, {
        # vox
        'url': 'http://www.nowtv.de/vox/der-hundeprofi/buero-fall-chihuahua-joel/player',
        'info_dict': {
            'id': '128953',
            'display_id': 'der-hundeprofi/buero-fall-chihuahua-joel',
            'ext': 'flv',
            'title': "Büro-Fall / Chihuahua 'Joel'",
            'description': 'md5:e62cb6bf7c3cc669179d4f1eb279ad8d',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1432408200,
            'upload_date': '20150523',
            'duration': 3092,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }, {
        'url': 'http://www.nowtv.de/rtl/bauer-sucht-frau/die-neuen-bauern-und-eine-hochzeit/preview',
        'only_matching': True,
    }, {
        'url': 'http://www.nowtv.at/rtl/bauer-sucht-frau/die-neuen-bauern-und-eine-hochzeit/preview?return=/rtl/bauer-sucht-frau/die-neuen-bauern-und-eine-hochzeit',
        'only_matching': True,
    }, {
        'url': 'http://www.nowtv.de/rtl2/echtzeit/list/aktuell/schnelles-geld-am-ende-der-welt/player',
        'only_matching': True,
    }, {
        'url': 'http://www.nowtv.de/rtl2/zuhause-im-glueck/jahr/2015/11/eine-erschuetternde-diagnose/player',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = '%s/%s' % (mobj.group('show_id'), mobj.group('id'))

        info = self._download_json(
            'https://api.nowtv.de/v3/movies/%s?fields=%s'
            % (display_id, ','.join(self._VIDEO_FIELDS)), display_id)

        return self._extract_video(info, display_id)


class NowTVListIE(NowTVBaseIE):
    _VALID_URL = r'https?://(?:www\.)?nowtv\.(?:de|at|ch)/(?:rtl|rtl2|rtlnitro|superrtl|ntv|vox)/(?P<show_id>[^/]+)/list/(?P<id>[^?/#&]+)$'

    _SHOW_FIELDS = ('title', )
    _SEASON_FIELDS = ('id', 'headline', 'seoheadline', )

    _TESTS = [{
        'url': 'http://www.nowtv.at/rtl/stern-tv/list/aktuell',
        'info_dict': {
            'id': '17006',
            'title': 'stern TV - Aktuell',
        },
        'playlist_count': 1,
    }, {
        'url': 'http://www.nowtv.at/rtl/das-supertalent/list/free-staffel-8',
        'info_dict': {
            'id': '20716',
            'title': 'Das Supertalent - FREE Staffel 8',
        },
        'playlist_count': 14,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        show_id = mobj.group('show_id')
        season_id = mobj.group('id')

        fields = []
        fields.extend(self._SHOW_FIELDS)
        fields.extend('formatTabs.%s' % field for field in self._SEASON_FIELDS)
        fields.extend(
            'formatTabs.formatTabPages.container.movies.%s' % field
            for field in self._VIDEO_FIELDS)

        list_info = self._download_json(
            'https://api.nowtv.de/v3/formats/seo?fields=%s&name=%s.php'
            % (','.join(fields), show_id),
            season_id)

        season = next(
            season for season in list_info['formatTabs']['items']
            if season.get('seoheadline') == season_id)

        title = '%s - %s' % (list_info['title'], season['headline'])

        entries = []
        for container in season['formatTabPages']['items']:
            for info in ((container.get('container') or {}).get('movies') or {}).get('items') or []:
                entries.append(self._extract_video(info))

        return self.playlist_result(
            entries, compat_str(season.get('id') or season_id), title)
