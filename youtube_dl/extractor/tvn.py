# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class TvnIE(InfoExtractor):
    IE_NAME = 'tvn.pl'
    _VALID_URL = r'https?://player\.pl/seriale-online/.*-odcinki,\d+/.*,.*,(?P<id>\d+)\.html.*'
    _API_URL = r'http://player.pl/api/?platform=ConnectedTV&terminal=Samsung&format=json&v=2.0&sort=newest&m=getItem&deviceScreenHeight=1080&deviceScreenWidth=1920&type=episode&authKey={}&id={}'
    _NETRC_MACHINE = 'tvn'
    _LOGIN_REQUIRED = True

    _TESTS = [{
        'url': 'http://player.pl/seriale-online/singielka-odcinki,3784/odcinek-10,S00E10,53103.html',
        'md5': '6f4c0e1181bd121c4880ed086fce46da',
        'info_dict': {
            'id': '53103',
            'ext': 'mp4',
            'title': 'Singielka.S00E10',
        },
    }]

    def _real_extract(self, url):
        (username, password) = self._get_login_info()
        if username is None:
            if self._LOGIN_REQUIRED:
                raise ExtractorError('API key not configured, needed for using %s.' % self.IE_NAME, expected=True)
            return
        video_id = self._match_id(url)
        episode_data = self._download_json(self._API_URL.format(password, video_id), video_id)

        title, thumbnail, formats, video_duration = '', '', [], 0
        if episode_data['status'] == 'success' and episode_data['item'].__len__() > 0:
            series_title = episode_data['item'].get('serie_title', None)
            title = "S{:0>2d}E{:0>2d}".format(int(episode_data['item'].get('season', 0)), int(episode_data['item'].get('episode', 0)))
            if series_title:
                title = '%s.%s' % (series_title, title)

            thumbnail = episode_data['item']['thumbnail'][0].get('url', '')
            video_duration = episode_data['item'].get('run_time', 0)
            videos_paths = episode_data['item']['videos']['main'].get('video_content', None)

            video_url = None
            for profile in ('HD', 'Bardzo wysoka', 'Wysoka', 'Standard', 'Średnia', 'Niska', 'Bardzo niska'):
                match = next((l for l in videos_paths if l['profile_name'] == profile), None)
                if match:
                    video_url = self._download_webpage(match['url'], video_id)
                    break
            formats = [{
                'format_id': 'direct',
                'url': video_url,
                'ext': 'mp4',
            }]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'duration': video_duration,
        }


class TvnSeriesIE(InfoExtractor):
    IE_NAME = 'tvn.pl:Series'
    _VALID_URL = r'https?://player\.pl/seriale-online/.*-odcinki,(?P<id>\d+)/$'
    _API_URL = r'http://player.pl/api/?platform=ConnectedTV&terminal=Samsung&format=json&v=2.0&sort=newest&m=getItems&limit=500&type=series&authKey={}&id={}'
    _NETRC_MACHINE = 'tvn'
    _LOGIN_REQUIRED = True

    _TESTS = [{
        'url': 'http://player.pl/seriale-online/singielka-odcinki,3784/',
        'info_dict': {
            'title': 'Singielka',
            'id': '3784',
        },
        'playlist_count': 4,
    }, {
        'url': 'http://player.pl/seriale-online/brzydula-odcinki,52/',
        'info_dict': {
            'title': 'Brzydula',
            'id': '84',
        },
        'playlist_count': 234,
    }]

    def _real_extract(self, url):
        (username, password) = self._get_login_info()
        if username is None:
            if self._LOGIN_REQUIRED:
                raise ExtractorError('API key not configured, needed for using %s.' % self.IE_NAME, expected=True)
            return

        series_id = self._match_id(url)
        series_data = self._download_json(self._API_URL.format(password, series_id), series_id)
        title, entries = '', []
        if series_data['status'] == 'success' and series_data['count_items'] > 0:
            title = series_data['items'][0].get('title', '')
            for v_path in series_data['items']:
                if v_path['type_episode'] != 'preview_prepremiere':
                    entries.append(self.url_result(
                            'http://player.pl/seriale-online/{}-odcinki,{}/odcinek-{},S{}E{},{}.html'.format(
                                title, series_id, v_path['episode'],v_path['season'],v_path['episode'], v_path['id']),
                            ie=TvnIE.ie_key()))

        return {
            '_type': 'playlist',
            'id': series_id,
            'title': title,
            'entries': entries,
        }
