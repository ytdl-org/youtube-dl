# coding: utf-8
from __future__ import unicode_literals

import itertools
import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    parse_iso8601,
)


class TwitchBaseIE(InfoExtractor):
    _VALID_URL_BASE = r'http://(?:www\.)?twitch\.tv'

    _API_BASE = 'https://api.twitch.tv'
    _LOGIN_URL = 'https://secure.twitch.tv/user/login'

    def _handle_error(self, response):
        if not isinstance(response, dict):
            return
        error = response.get('error')
        if error:
            raise ExtractorError(
                '%s returned error: %s - %s' % (self.IE_NAME, error, response.get('message')),
                expected=True)

    def _download_json(self, url, video_id, note='Downloading JSON metadata'):
        response = super(TwitchBaseIE, self)._download_json(url, video_id, note)
        self._handle_error(response)
        return response

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_page = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading login page')

        authenticity_token = self._search_regex(
            r'<input name="authenticity_token" type="hidden" value="([^"]+)"',
            login_page, 'authenticity token')

        login_form = {
            'utf8': '✓'.encode('utf-8'),
            'authenticity_token': authenticity_token,
            'redirect_on_login': '',
            'embed_form': 'false',
            'mp_source_action': '',
            'follow': '',
            'user[login]': username,
            'user[password]': password,
        }

        request = compat_urllib_request.Request(
            self._LOGIN_URL, compat_urllib_parse.urlencode(login_form).encode('utf-8'))
        request.add_header('Referer', self._LOGIN_URL)
        response = self._download_webpage(
            request, None, 'Logging in as %s' % username)

        m = re.search(
            r"id=([\"'])login_error_message\1[^>]*>(?P<msg>[^<]+)", response)
        if m:
            raise ExtractorError(
                'Unable to login: %s' % m.group('msg').strip(), expected=True)


class TwitchItemBaseIE(TwitchBaseIE):
    def _download_info(self, item, item_id):
        return self._extract_info(self._download_json(
            '%s/kraken/videos/%s%s' % (self._API_BASE, item, item_id), item_id,
            'Downloading %s info JSON' % self._ITEM_TYPE))

    def _extract_media(self, item_id):
        info = self._download_info(self._ITEM_SHORTCUT, item_id)
        response = self._download_json(
            '%s/api/videos/%s%s' % (self._API_BASE, self._ITEM_SHORTCUT, item_id), item_id,
            'Downloading %s playlist JSON' % self._ITEM_TYPE)
        entries = []
        chunks = response['chunks']
        qualities = list(chunks.keys())
        for num, fragment in enumerate(zip(*chunks.values()), start=1):
            formats = []
            for fmt_num, fragment_fmt in enumerate(fragment):
                format_id = qualities[fmt_num]
                fmt = {
                    'url': fragment_fmt['url'],
                    'format_id': format_id,
                    'quality': 1 if format_id == 'live' else 0,
                }
                m = re.search(r'^(?P<height>\d+)[Pp]', format_id)
                if m:
                    fmt['height'] = int(m.group('height'))
                formats.append(fmt)
            self._sort_formats(formats)
            entry = dict(info)
            entry['id'] = '%s_%d' % (entry['id'], num)
            entry['title'] = '%s part %d' % (entry['title'], num)
            entry['formats'] = formats
            entries.append(entry)
        return self.playlist_result(entries, info['id'], info['title'])

    def _extract_info(self, info):
        return {
            'id': info['_id'],
            'title': info['title'],
            'description': info['description'],
            'duration': info['length'],
            'thumbnail': info['preview'],
            'uploader': info['channel']['display_name'],
            'uploader_id': info['channel']['name'],
            'timestamp': parse_iso8601(info['recorded_at']),
            'view_count': info['views'],
        }

    def _real_extract(self, url):
        return self._extract_media(self._match_id(url))


class TwitchVideoIE(TwitchItemBaseIE):
    IE_NAME = 'twitch:video'
    _VALID_URL = r'%s/[^/]+/b/(?P<id>[^/]+)' % TwitchBaseIE._VALID_URL_BASE
    _ITEM_TYPE = 'video'
    _ITEM_SHORTCUT = 'a'

    _TEST = {
        'url': 'http://www.twitch.tv/riotgames/b/577357806',
        'info_dict': {
            'id': 'a577357806',
            'title': 'Worlds Semifinals - Star Horn Royal Club vs. OMG',
        },
        'playlist_mincount': 12,
    }


class TwitchChapterIE(TwitchItemBaseIE):
    IE_NAME = 'twitch:chapter'
    _VALID_URL = r'%s/[^/]+/c/(?P<id>[^/]+)' % TwitchBaseIE._VALID_URL_BASE
    _ITEM_TYPE = 'chapter'
    _ITEM_SHORTCUT = 'c'

    _TEST = {
        'url': 'http://www.twitch.tv/acracingleague/c/5285812',
        'info_dict': {
            'id': 'c5285812',
            'title': 'ACRL Off Season - Sports Cars @ Nordschleife',
        },
        'playlist_mincount': 3,
    }


class TwitchVodIE(TwitchItemBaseIE):
    IE_NAME = 'twitch:vod'
    _VALID_URL = r'%s/[^/]+/v/(?P<id>[^/]+)' % TwitchBaseIE._VALID_URL_BASE
    _ITEM_TYPE = 'vod'
    _ITEM_SHORTCUT = 'v'

    _TEST = {
        'url': 'http://www.twitch.tv/ksptv/v/3622000',
        'info_dict': {
            'id': 'v3622000',
            'ext': 'mp4',
            'title': '''KSPTV: Squadcast: "Everyone's on vacation so here's Dahud" Edition!''',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 6951,
            'timestamp': 1419028564,
            'upload_date': '20141219',
            'uploader': 'KSPTV',
            'uploader_id': 'ksptv',
            'view_count': int,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        item_id = self._match_id(url)
        info = self._download_info(self._ITEM_SHORTCUT, item_id)
        access_token = self._download_json(
            '%s/api/vods/%s/access_token' % (self._API_BASE, item_id), item_id,
            'Downloading %s access token' % self._ITEM_TYPE)
        formats = self._extract_m3u8_formats(
            'http://usher.twitch.tv/vod/%s?nauth=%s&nauthsig=%s'
            % (item_id, access_token['token'], access_token['sig']),
            item_id, 'mp4')
        info['formats'] = formats
        return info


class TwitchPlaylistBaseIE(TwitchBaseIE):
    _PLAYLIST_URL = '%s/kraken/channels/%%s/videos/?offset=%%d&limit=%%d' % TwitchBaseIE._API_BASE
    _PAGE_LIMIT = 100

    def _extract_playlist(self, channel_id):
        info = self._download_json(
            '%s/kraken/channels/%s' % (self._API_BASE, channel_id),
            channel_id, 'Downloading channel info JSON')
        channel_name = info.get('display_name') or info.get('name')
        entries = []
        offset = 0
        limit = self._PAGE_LIMIT
        for counter in itertools.count(1):
            response = self._download_json(
                self._PLAYLIST_URL % (channel_id, offset, limit),
                channel_id, 'Downloading %s videos JSON page %d' % (self._PLAYLIST_TYPE, counter))
            videos = response['videos']
            if not videos:
                break
            entries.extend([self.url_result(video['url']) for video in videos])
            offset += limit
        return self.playlist_result(entries, channel_id, channel_name)

    def _real_extract(self, url):
        return self._extract_playlist(self._match_id(url))


class TwitchProfileIE(TwitchPlaylistBaseIE):
    IE_NAME = 'twitch:profile'
    _VALID_URL = r'%s/(?P<id>[^/]+)/profile/?(?:\#.*)?$' % TwitchBaseIE._VALID_URL_BASE
    _PLAYLIST_TYPE = 'profile'

    _TEST = {
        'url': 'http://www.twitch.tv/vanillatv/profile',
        'info_dict': {
            'id': 'vanillatv',
            'title': 'VanillaTV',
        },
        'playlist_mincount': 412,
    }


class TwitchPastBroadcastsIE(TwitchPlaylistBaseIE):
    IE_NAME = 'twitch:past_broadcasts'
    _VALID_URL = r'%s/(?P<id>[^/]+)/profile/past_broadcasts/?(?:\#.*)?$' % TwitchBaseIE._VALID_URL_BASE
    _PLAYLIST_URL = TwitchPlaylistBaseIE._PLAYLIST_URL + '&broadcasts=true'
    _PLAYLIST_TYPE = 'past broadcasts'

    _TEST = {
        'url': 'http://www.twitch.tv/spamfish/profile/past_broadcasts',
        'info_dict': {
            'id': 'spamfish',
            'title': 'Spamfish',
        },
        'playlist_mincount': 54,
    }
