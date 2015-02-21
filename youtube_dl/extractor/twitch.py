# coding: utf-8
from __future__ import unicode_literals

import itertools
import re
import random

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    parse_iso8601,
)


class TwitchBaseIE(InfoExtractor):
    _VALID_URL_BASE = r'https?://(?:www\.)?twitch\.tv'

    _API_BASE = 'https://api.twitch.tv'
    _USHER_BASE = 'http://usher.twitch.tv'
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

    _TESTS = [{
        'url': 'http://www.twitch.tv/acracingleague/c/5285812',
        'info_dict': {
            'id': 'c5285812',
            'title': 'ACRL Off Season - Sports Cars @ Nordschleife',
        },
        'playlist_mincount': 3,
    }, {
        'url': 'http://www.twitch.tv/tsm_theoddone/c/2349361',
        'only_matching': True,
    }]


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
            '%s/vod/%s?nauth=%s&nauthsig=%s'
            % (self._USHER_BASE, item_id, access_token['token'], access_token['sig']),
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
            page_entries = self._extract_playlist_page(response)
            if not page_entries:
                break
            entries.extend(page_entries)
            offset += limit
        return self.playlist_result(
            [self.url_result(entry) for entry in set(entries)],
            channel_id, channel_name)

    def _extract_playlist_page(self, response):
        videos = response.get('videos')
        return [video['url'] for video in videos] if videos else []

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


class TwitchBookmarksIE(TwitchPlaylistBaseIE):
    IE_NAME = 'twitch:bookmarks'
    _VALID_URL = r'%s/(?P<id>[^/]+)/profile/bookmarks/?(?:\#.*)?$' % TwitchBaseIE._VALID_URL_BASE
    _PLAYLIST_URL = '%s/api/bookmark/?user=%%s&offset=%%d&limit=%%d' % TwitchBaseIE._API_BASE
    _PLAYLIST_TYPE = 'bookmarks'

    _TEST = {
        'url': 'http://www.twitch.tv/ognos/profile/bookmarks',
        'info_dict': {
            'id': 'ognos',
            'title': 'Ognos',
        },
        'playlist_mincount': 3,
    }

    def _extract_playlist_page(self, response):
        entries = []
        for bookmark in response.get('bookmarks', []):
            video = bookmark.get('video')
            if not video:
                continue
            entries.append(video['url'])
        return entries


class TwitchStreamIE(TwitchBaseIE):
    IE_NAME = 'twitch:stream'
    _VALID_URL = r'%s/(?P<id>[^/]+)/?(?:\#.*)?$' % TwitchBaseIE._VALID_URL_BASE

    _TEST = {
        'url': 'http://www.twitch.tv/shroomztv',
        'info_dict': {
            'id': '12772022048',
            'display_id': 'shroomztv',
            'ext': 'mp4',
            'title': 're:^ShroomzTV [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'H1Z1 - lonewolfing with ShroomzTV | A3 Battle Royale later - @ShroomzTV',
            'is_live': True,
            'timestamp': 1421928037,
            'upload_date': '20150122',
            'uploader': 'ShroomzTV',
            'uploader_id': 'shroomztv',
            'view_count': int,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        stream = self._download_json(
            '%s/kraken/streams/%s' % (self._API_BASE, channel_id), channel_id,
            'Downloading stream JSON').get('stream')

        # Fallback on profile extraction if stream is offline
        if not stream:
            return self.url_result(
                'http://www.twitch.tv/%s/profile' % channel_id,
                'TwitchProfile', channel_id)

        access_token = self._download_json(
            '%s/api/channels/%s/access_token' % (self._API_BASE, channel_id), channel_id,
            'Downloading channel access token')

        query = {
            'allow_source': 'true',
            'p': random.randint(1000000, 10000000),
            'player': 'twitchweb',
            'segment_preference': '4',
            'sig': access_token['sig'],
            'token': access_token['token'],
        }

        formats = self._extract_m3u8_formats(
            '%s/api/channel/hls/%s.m3u8?%s'
            % (self._USHER_BASE, channel_id, compat_urllib_parse.urlencode(query).encode('utf-8')),
            channel_id, 'mp4')

        # prefer the 'source' stream, the others are limited to 30 fps
        def _sort_source(f):
            if f.get('m3u8_media') is not None and f['m3u8_media'].get('NAME') == 'Source':
                return 1
            return 0
        formats = sorted(formats, key=_sort_source)

        view_count = stream.get('viewers')
        timestamp = parse_iso8601(stream.get('created_at'))

        channel = stream['channel']
        title = self._live_title(channel.get('display_name') or channel.get('name'))
        description = channel.get('status')

        thumbnails = []
        for thumbnail_key, thumbnail_url in stream['preview'].items():
            m = re.search(r'(?P<width>\d+)x(?P<height>\d+)\.jpg$', thumbnail_key)
            if not m:
                continue
            thumbnails.append({
                'url': thumbnail_url,
                'width': int(m.group('width')),
                'height': int(m.group('height')),
            })

        return {
            'id': compat_str(stream['_id']),
            'display_id': channel_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'uploader': channel.get('display_name'),
            'uploader_id': channel.get('name'),
            'timestamp': timestamp,
            'view_count': view_count,
            'formats': formats,
            'is_live': True,
        }
