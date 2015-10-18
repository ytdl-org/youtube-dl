# coding: utf-8
from __future__ import unicode_literals

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

class NowTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nowtv\.(?:de|at|ch)/(?:rtl|rtl2|rtlnitro|superrtl|ntv|vox)/(?P<id>.+?)$'
    _TESTS = [{
        # rtl
        'url': 'http://www.nowtv.de/rtl/bauer-sucht-frau/die-neuen-bauern-und-eine-hochzeit/player',
        'info_dict': {
            'id': '203519',
            'display_id': 'bauer-sucht-frau/die-neuen-bauern-und-eine-hochzeit',
            'ext': 'flv',
            'title': 'Die neuen Bauern und eine Hochzeit',
            'description': 'md5:e234e1ed6d63cf06be5c070442612e7e',
            'thumbnail': 're:^https?://.*\.jpg$',
            'timestamp': 1432580700,
            'upload_date': '20150525',
            'duration': 2786,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
        # rtl
        'url': 'http://www.nowtv.at/rtl/stern-tv/list/aktuell',
        'info_dict': {
            'title': 'stern TV',
            'id': '2385',
        },
        # rtl
        'url': 'http://www.nowtv.at/rtl/das-supertalent/list/free-staffel-8',
        'info_dict': {
            'title': 'Das Supertalent',
            'id': '46',
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
            'thumbnail': 're:^https?://.*\.jpg$',
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
            'thumbnail': 're:^https?://.*\.jpg$',
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
            'thumbnail': 're:^https?://.*\.jpg$',
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
            'thumbnail': 're:^https?://.*\.jpg$',
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
            'thumbnail': 're:^https?://.*\.jpg$',
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
    }]

    def _real_extract(self, url):
        url = url.split('?')[0]
        display_id = self._match_id(url)
        display_id_split = display_id.split('/')

        if 'player' in url or 'preview' in url: # then the link is a direct videoclip-link!
            if len(display_id_split) > 2:
                display_id = '/'.join((display_id_split[0], display_id_split[-2]))
            return self._extract_videoclip(display_id)
        else:
            season = None
            if len(display_id_split) > 1:
                display_id = display_id_split[0]
                season = display_id_split[2]
            return self._extract_playlist(display_id, season)

    def _extract_videoclip(self, display_id):
        info = self._download_json(
            'https://api.nowtv.de/v3/movies/%s?fields=id,title,season,episode,free,geoblocked,articleLong,articleShort,broadcastStartDate,seoUrl,duration,format,files' % display_id,
            display_id)

        video_id, title, title_long, description, timestamp, duration, formats = self.episode_details(info)

        f = info.get('format', {})
        thumbnail = f.get('defaultImage169Format') or f.get('defaultImage169Logo')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': '%s - %s' % (info['format']['title'], title),
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }

    def _extract_playlist(self, display_id, season):
        info = self._download_json(
            'https://api.nowtv.de/v3/formats/seo?fields=id,title,defaultImage169Format,defaultImage169Logo,formatTabs.*,formatTabs.formatTabPages.container.movies.*,formatTabs.formatTabPages.container.movies.files&name=%s.php' % display_id,
            display_id)

        playlist_id = info['id']
        playlist_title = info['title']
        thumbnail = info.get('defaultImage169Format') or info.get('defaultImage169Logo')

        files = info['formatTabs']

        videos = []
        playlists = []

        for season_item in files['items']:
            if season:
                if season != season_item['seoheadline']:
                    continue

            for items in season_item['formatTabPages']['items']:
                try:
                    for episode in items['container']['movies']['items']:

                        video_id, title, title_long, description, timestamp, duration, formats = self.episode_details(episode)

                        videos.append({
                            'id': video_id,
                            'display_id': display_id,
                            'title': title_long,
                            'description': description,
                            'thumbnail': thumbnail,
                            'timestamp': timestamp,
                            'duration': duration,
                            'formats': formats,
                        })
                except:
                    continue

        return self.playlist_result(videos.reverse(), playlist_id, playlist_title)

    def episode_details(self, info):

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

        description = info.get('articleLong') or info.get('articleShort')
        timestamp = parse_iso8601(info.get('broadcastStartDate'), ' ')
        duration = parse_duration(info.get('duration'))
        title = info['title']
        title_long = "S%sE%s - %s" % (info['season'], info['episode'], title)

        return video_id, title, title_long, description, timestamp, duration, formats
