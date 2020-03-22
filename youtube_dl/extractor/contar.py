# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    urlencode_postdata,
    ExtractorError,
)


class ContarBaseIE(InfoExtractor):

    _UUID_RE = r'[\da-fA-F]{8}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{12}'
    _NETRC_MACHINE = 'contar'
    _API_BASE = 'https://api.cont.ar/api/v2/'

    def _handle_errors(self, result):
        error = result.get('error', {}).get('message')
        if error:
            if isinstance(error, dict):
                error = ', '.join(error.values())
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, error), expected=True)

    def _call_api(self, path, video_id, headers={}, note='Downloading JSON metadata'):
        if self._auth_token:
            headers['Authorization'] = 'Bearer ' + self._auth_token

        result = self._download_json(
            self._API_BASE + path, video_id, headers=headers, note=note)

        self._handle_errors(result)
        return result.get('data', [])

    def _real_initialize(self):
        email, password = self._get_login_info()
        if email is None:
            self.raise_login_required()

        result = self._download_json(
            self._API_BASE + 'authenticate', None, data=urlencode_postdata({
                'email': email,
                'password': password,
            }))

        self._handle_errors(result)
        self._auth_token = result.get('token')

    def _get_video_info(self, video, video_id, base={}):

        formats = self._get_formats(video.get('streams', []), video.get('id'))
        subtitles = self._get_subtitles(video.get('subtitles', []).get('data', []), video.get('id'))

        serie_info = base.get('serie_info') or self._get_serie_info(video.get('serie'))
        season_number = base.get('season_number') or self._get_season_number(serie_info, video.get('id'))
        episode_number = video.get('episode')

        info = {
            'id': video.get('id'),
            'title': video.get('name'),
            'description': video.get('synopsis'),
            'series': video.get('serie_name'),
            'episode': video.get('name'),
            'episode_number': int_or_none(episode_number),
            'season_number': int_or_none(season_number),
            'season_id': video.get('serie'),
            'episode_id': video.get('id'),
            'duration': int_or_none(video.get('length')),
            'thumbnail': video.get('posterImage'),
            'release_year': int_or_none(serie_info.get('year')),
            # 'timestamp': timestamp,
            'formats': formats,
            'subtitles': subtitles,
        }

        return info

    def _get_serie_info(self, serie_id, headers={}):
        serie = self._call_api('serie/' + serie_id, serie_id, headers=headers, note='Downloading Serie JSON metadata')
        return serie

    def _get_season_number(self, serie_info, video_id):
        for season in serie_info.get('seasons', []).get('data', []):
            season_number = season.get('name')
            for episode in season.get('videos', []).get('data', []):
                if episode.get('id') == video_id:
                    return season_number
        return None

    def _get_subtitles(self, subtitles, video_id):
        subs = {}
        for sub in subtitles:
            lang = sub.get('lang').lower()
            subs[lang] = [{'url': sub.get('url'), 'ext': 'srt'}]

        return subs

    def _get_formats(self, videos, video_id):
        formats = []
        for stream in videos:
            stream_url = stream.get('url')
            type = stream.get('type')
            if (type == 'HLS'):
                formats.extend(self._extract_m3u8_formats(stream_url,
                                                          video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls',
                                                          fatal=False))
            elif (type == 'DASH'):
                formats.extend(self._extract_mpd_formats(
                    stream_url, video_id, mpd_id='dash', fatal=False))

        self._sort_formats(formats)
        return formats


class ContarIE(ContarBaseIE):

    _VALID_URL = r'https?://(?:www\.)?cont\.ar/watch/(?P<id>%s)' % ContarBaseIE._UUID_RE
    _TEST = {
        'url': 'https://www.cont.ar/watch/d2815f05-f52f-499f-90d0-5671e9e71ce8',
        'md5': '72cfee8799d964291433004c557d0b2b',
        'info_dict': {
            'id': 'd2815f05-f52f-499f-90d0-5671e9e71ce8',
            'ext': 'mp4',
            'title': 'md5:305bc22419c1f4c3ce596e03e725498b',
            'duration': 648,
            'release_year': 2016,
            'description': 'md5:fb359bdf6ab3d4c01330b4d31d715403',
            'season_number': 1,
            'episode_number': 1,
        },
        'params': {
            'username': 'ytdl@yt-dl.org',
            'password': '(snip)',
            'format': 'hls-4755-1'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._call_api('videos/' + video_id, video_id, headers={'Referer': url})
        info = self._get_video_info(video, video_id)
        return info


class ContarSerieIE(ContarBaseIE):

    _VALID_URL = r'https?://(?:www\.)?cont\.ar/serie/(?P<id>%s)' % ContarBaseIE._UUID_RE
    _TEST = {
        'url': 'https://www.cont.ar/serie/353247d5-da97-4cb6-8571-c4fbab28c643',
        'info_dict': {
            'id': '353247d5-da97-4cb6-8571-c4fbab28c643',
            'title': 'md5:a387a67af353212f7499ce3a045a86de',
            'description': 'md5:fb14968784f8d6ba0a50a53218ad0538'
        },
        'playlist_count': 11,
        'playlist': [{
            'md5': '651e129bae9f7ee7c4c83e1263b26828',
            'info_dict': {
                'id': '3414c62f-7b40-439e-b74d-1dd9b0190808',
                'ext': 'mp4',
                'title': 'md5:d5c7d8adf4223d7856d0f8d959f6bff7',
                'duration': 3185,
                'release_year': 2018,
                'description': 'md5:94ccc2f57721514ce04e514116e914fa',
                'season_number': 1,
                'episode_number': 11,
            },
            'params': {
                'username': 'ytdl@yt-dl.org',
                'password': '(snip)',
                'format': 'bestvideo',
            }
        }, {
            'md5': '5b80df03801c2399f62da223f16bb801',
            'info_dict': {
                'id': '5972ae9a-43fe-4056-81bc-ab963c057cc6',
                'ext': 'mp4',
                'title': 'md5:64f243a753953726ddc39336e1c2f361',
                'release_year': 2018,
                'duration': 3052,
                'description': 'md5:87e1bfbd5ed02808b73f63f2c9a0722d',
                'season_number': 1,
                'episode_number': 3
            },
            'params': {
                'skip_download': True,
            },
        }],
        'params': {
            'username': 'ytdl@yt-dl.org',
            'password': '(snip)',
            'format': 'bestvideo',
        }
    }

    def _real_extract(self, url):
        serie_id = self._match_id(url)

        serie_info = self._get_serie_info(serie_id, headers={'Referer': url})

        entries = []

        base = {}
        base['serie_info'] = serie_info

        for season in serie_info.get('seasons', []).get('data', []):
            base['season_number'] = season.get('name')
            for episode in season.get('videos', []).get('data', []):
                info = self._get_video_info(episode, serie_id, base)
                entries.append(info)

        return self.playlist_result(
            entries, serie_id,
            serie_info.get('name'), serie_info.get('story_large'))


class ContarChannelIE(ContarBaseIE):

    _VALID_URL = r'https?://(?:www\.)?cont\.ar/channel/(?P<id>\d+)'
    _TEST = {
        'url': 'https://www.cont.ar/channel/242',
        'info_dict': {
            'id': '242',
            'title': 'md5:352d30d8fa7896eec02f65b2c7299d27',
            'description': 'md5:ac4e1f02201cffb86ac8ed4bcba4a593'
        },
        'playlist_mincount': 68,
        'params': {
            'usenetrc': True,
            'skip_download': True
        }
    }

    def _real_extract(self, url):
        list_id = self._match_id(url)
        channel_info = self._call_api('channel/info/' + list_id, list_id, headers={'Referer': url}, note='Downloading Channel Info JSON metadata')
        list = self._call_api('channel/series/' + list_id, list_id, headers={'Referer': url}, note='Downloading Channel List JSON metadata')
        entries = []

        for video in list:
            if (video.get('type') == 'SERIE'):
                url = 'www.cont.ar/serie/%s' % video.get('uuid')
                entries.append(self.url_result(url, video_id=video.get('uuid'), video_title=video.get('name')))

        return self.playlist_result(
            entries, list_id, channel_info.get('name'), channel_info.get('description'))


class ContarBrowseIE(ContarBaseIE):

    _VALID_URL = r'https?://(?:www\.)?cont\.ar/browse/genre/(?P<id>\d+)'
    _TEST = {
        'url': 'https://www.cont.ar/browse/genre/46',
        'info_dict': {
            'id': '46',
            'title': 'md5:41dd5b7c28b8b53c32341151e750d367',
        },
        'playlist_mincount': 65,
        'params': {
            'username': 'ytdl@yt-dl.org',
            'password': '(snip)',
            'skip_download': True
        }
    }

    def _real_extract(self, url):
        list_id = self._match_id(url)

        list = self._call_api('full/section/' + list_id, list_id, headers={'Referer': url})
        entries = []

        for video in list.get('videos', []).get('data', []):
            if (video.get('type') == 'SERIE'):
                url = 'www.cont.ar/serie/%s' % video.get('uuid')
                entries.append(self.url_result(url, video_id=video.get('uuid'), video_title=video.get('name')))

        return self.playlist_result(
            entries, list_id,
            list.get('title'))
