# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    get_element_by_class,
    int_or_none,
    parse_iso8601,
    str_or_none,
    strip_or_none,
    try_get,
    urlencode_postdata,
)


class VidioBaseIE(InfoExtractor):
    _LOGIN_URL = 'https://www.vidio.com/users/login'
    _NETRC_MACHINE = 'vidio'

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        def is_logged_in():
            res = self._download_json(
                'https://www.vidio.com/interactions.json', None, 'Checking if logged in', fatal=False) or {}
            return bool(res.get('current_user'))

        if is_logged_in():
            return

        login_page = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading log in page')

        login_form = self._form_hidden_inputs("login-form", login_page)
        login_form.update({
            'user[login]': username,
            'user[password]': password,
        })
        login_post, login_post_urlh = self._download_webpage_handle(
            self._LOGIN_URL, None, 'Logging in', data=urlencode_postdata(login_form), expected_status=[302, 401])

        if login_post_urlh.status == 401:
            reason = get_element_by_class('onboarding-form__general-error', login_post)
            if reason:
                raise ExtractorError(
                    'Unable to log in: %s' % reason, expected=True)
            raise ExtractorError('Unable to log in')

    def _real_initialize(self):
        self._api_key = self._download_json(
            'https://www.vidio.com/auth', None, data=b'')['api_key']
        self._login()

    def _call_api(self, url, video_id, note=None):
        return self._download_json(url, video_id, note=note, headers={
            'Content-Type': 'application/vnd.api+json',
            'X-API-KEY': self._api_key,
        })


class VidioIE(VidioBaseIE):
    _VALID_URL = r'https?://(?:www\.)?vidio\.com/watch/(?P<id>\d+)-(?P<display_id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://www.vidio.com/watch/165683-dj_ambred-booyah-live-2015',
        'md5': 'cd2801394afc164e9775db6a140b91fe',
        'info_dict': {
            'id': '165683',
            'display_id': 'dj_ambred-booyah-live-2015',
            'ext': 'mp4',
            'title': 'DJ_AMBRED - Booyah (Live 2015)',
            'description': 'md5:27dc15f819b6a78a626490881adbadf8',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 149,
            'like_count': int,
            'uploader': 'TWELVE Pic',
            'timestamp': 1444902800,
            'upload_date': '20151015',
            'uploader_id': 'twelvepictures',
            'channel': 'Cover Music Video',
            'channel_id': '280236',
            'view_count': int,
            'dislike_count': int,
            'comment_count': int,
            'tags': 'count:4',
        },
    }, {
        'url': 'https://www.vidio.com/watch/77949-south-korea-test-fires-missile-that-can-strike-all-of-the-north',
        'only_matching': True,
    }, {
        # Premier-exclusive video
        'url': 'https://www.vidio.com/watch/1550718-stand-by-me-doraemon',
        'only_matching': True
    }]

    def _real_extract(self, url):
        video_id, display_id = re.match(self._VALID_URL, url).groups()
        data = self._call_api('https://api.vidio.com/videos/' + video_id, display_id)
        video = data['videos'][0]
        title = video['title'].strip()
        is_premium = video.get('is_premium')

        if is_premium:
            sources = self._download_json(
                'https://www.vidio.com/interactions_stream.json?video_id=%s&type=videos' % video_id,
                display_id, note='Downloading premier API JSON')
            if not (sources.get('source') or sources.get('source_dash')):
                self.raise_login_required('This video is only available for registered users with the appropriate subscription')

            formats = []
            if sources.get('source'):
                formats.extend(self._extract_m3u8_formats(
                    sources['source'], display_id, 'mp4', 'm3u8_native'))
            if sources.get('source_dash'):  # TODO: Find video example with source_dash
                formats.extend(self._extract_mpd_formats(
                    sources['source_dash'], display_id, 'dash'))
        else:
            hls_url = data['clips'][0]['hls_url']
            formats = self._extract_m3u8_formats(
                hls_url, display_id, 'mp4', 'm3u8_native')

        self._sort_formats(formats)

        get_first = lambda x: try_get(data, lambda y: y[x + 's'][0], dict) or {}
        channel = get_first('channel')
        user = get_first('user')
        username = user.get('username')
        get_count = lambda x: int_or_none(video.get('total_' + x))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': strip_or_none(video.get('description')),
            'thumbnail': video.get('image_url_medium'),
            'duration': int_or_none(video.get('duration')),
            'like_count': get_count('likes'),
            'formats': formats,
            'uploader': user.get('name'),
            'timestamp': parse_iso8601(video.get('created_at')),
            'uploader_id': username,
            'uploader_url': 'https://www.vidio.com/@' + username if username else None,
            'channel': channel.get('name'),
            'channel_id': str_or_none(channel.get('id')),
            'view_count': get_count('view_count'),
            'dislike_count': get_count('dislikes'),
            'comment_count': get_count('comments'),
            'tags': video.get('tag_list'),
        }


class VidioPremierIE(VidioBaseIE):
    _VALID_URL = r'https?://(?:www\.)?vidio\.com/premier/(?P<id>\d+)/(?P<display_id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.vidio.com/premier/2885/badai-pasti-berlalu',
        'playlist_mincount': 14,
    }, {
        # Series with both free and premier-exclusive videos
        'url': 'https://www.vidio.com/premier/2567/sosmed',
        'only_matching': True,
    }]

    def _playlist_entries(self, playlist, series_id, series_name, season_name, display_id):
        playlist_url = 'https://api.vidio.com/content_profiles/%s/playlists/%s/playlist_items' % (series_id, playlist['id'])

        entries = []
        index = 1
        episode_index = 1
        while playlist_url:
            playlist_json = self._call_api(playlist_url, display_id, 'Downloading API JSON page %s' % index)
            for video_json in playlist_json.get('data', []):
                link = video_json['links']['watchpage']
                result = self.url_result(link, 'Vidio', video_json['id'])
                result.update({
                    'series': series_name,
                    'season': season_name,
                    'episode': try_get(video_json, lambda x: x['attributes']['title']),
                    'episode_number': episode_index,
                })
                entries.append(result)
                episode_index += 1
            playlist_url = try_get(playlist_json, lambda x: x['links']['next'])
            index += 1
        return entries

    def _real_extract(self, url):
        premier_id, display_id = re.match(self._VALID_URL, url).groups()
        entries = []
        playlist_data = self._call_api('https://www.vidio.com/api/series/%s' % premier_id, display_id)
        # While the video entries are embedded within the series JSON metadata, they're (accidentally?) truncated on really long playlists so content profile API is still used
        for playlist in playlist_data.get('seasons', []):
            entries.extend(self._playlist_entries(
                playlist, premier_id, playlist_data.get('title'), playlist.get('name'), display_id))
        return self.playlist_result(
            entries, premier_id, playlist_data.get('title'), playlist_data.get('description'))


class VidioLiveIE(VidioBaseIE):
    _VALID_URL = r'https?://(?:www\.)?vidio\.com/live/(?P<id>\d+)-(?P<display_id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.vidio.com/live/204-sctv',
        'info_dict': {
            'id': '204',
            'title': 'SCTV',
            'uploader': 'SCTV',
            'uploader_id': 'sctv',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        # Premier-exclusive livestream
        'url': 'https://www.vidio.com/live/6362-tvn',
        'only_matching': True,
    }, {
        # DRM premier-exclusive livestream
        'url': 'https://www.vidio.com/live/6299-bein-1',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id, display_id = re.match(self._VALID_URL, url).groups()
        stream_data = self._call_api(
            'https://www.vidio.com/api/livestreamings/%s/detail' % video_id, display_id)
        stream_meta = stream_data['livestreamings'][0]
        user = stream_data.get('users', [{}])[0]

        title = stream_meta.get('title')
        username = user.get('username')

        formats = []
        if stream_meta.get('is_drm'):
            self.raise_no_formats(
                'This video is DRM protected.', expected=True)

        if stream_meta.get('is_premium'):
            sources = self._download_json(
                'https://www.vidio.com/interactions_stream.json?video_id=%s&type=livestreamings' % video_id,
                display_id, note='Downloading premier API JSON')
            if not (sources.get('source') or sources.get('source_dash')):
                self.raise_login_required('This video is only available for registered users with the appropriate subscription')

            if sources.get('source'):
                token_json = self._download_json(
                    'https://www.vidio.com/live/%s/tokens' % video_id,
                    display_id, note='Downloading HLS token JSON', data=b'')
                formats.extend(self._extract_m3u8_formats(
                    sources['source'] + '?' + token_json.get('token', ''), display_id, 'mp4', 'm3u8_native'))
            if sources.get('source_dash'):
                pass
        else:
            if stream_meta.get('stream_token_url'):
                token_json = self._download_json(
                    'https://www.vidio.com/live/%s/tokens' % video_id,
                    display_id, note='Downloading HLS token JSON', data=b'')
                formats.extend(self._extract_m3u8_formats(
                    stream_meta['stream_token_url'] + '?' + token_json.get('token', ''), display_id, 'mp4', 'm3u8_native'))
            if stream_meta.get('stream_dash_url'):
                pass
            if stream_meta.get('stream_url'):
                formats.extend(self._extract_m3u8_formats(
                    stream_meta['stream_url'], display_id, 'mp4', 'm3u8_native'))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'is_live': True,
            'description': strip_or_none(stream_meta.get('description')),
            'thumbnail': stream_meta.get('image'),
            'like_count': int_or_none(stream_meta.get('like')),
            'dislike_count': int_or_none(stream_meta.get('dislike')),
            'formats': formats,
            'uploader': user.get('name'),
            'timestamp': parse_iso8601(stream_meta.get('start_time')),
            'uploader_id': username,
            'uploader_url': 'https://www.vidio.com/@' + username if username else None,
        }
