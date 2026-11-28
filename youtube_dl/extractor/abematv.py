# coding: utf-8
from __future__ import unicode_literals

import base64
import binascii
import functools
import hashlib
import hmac
import json
import re
import sys
import time
import uuid

from .common import InfoExtractor
from ..aes import aes_ecb_encrypt, key_expansion, aes_decrypt
from ..compat import (
    compat_str,
    compat_urllib_request,
    compat_urllib_error,
    compat_urllib_parse,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    ExtractorError,
    OnDemandPagedList,
    int_or_none,
    try_get,
    update_url_query,
)


# ---------------------------------------------------------------------------
# AES-ECB decryption
# youtube-dl's aes.py ships aes_ecb_encrypt but not aes_ecb_decrypt.
# ECB decryption is simply calling aes_decrypt on each 16-byte block.
# ---------------------------------------------------------------------------

_BLOCK_SIZE = 16


def _aes_ecb_decrypt(data, key):
    """
    Decrypt with AES in ECB mode (no padding removal, raw block cipher).

    @param {int[]} data   ciphertext (must be a multiple of 16 bytes)
    @param {int[]} key    16/24/32-byte key
    @returns {int[]}      plaintext
    """
    expanded_key = key_expansion(key)
    out = []
    for block_start in range(0, len(data), _BLOCK_SIZE):
        block = data[block_start:block_start + _BLOCK_SIZE]
        out += aes_decrypt(block, expanded_key)
    return out


# ---------------------------------------------------------------------------
# decode_base_n — yt-dlp utility, not present in youtube-dl
# ---------------------------------------------------------------------------

def _decode_base_n(string, n=None, table=None):
    """Decode a string in an arbitrary base, given a character table."""
    if not table:
        table = '0123456789abcdefghijklmnopqrstuvwxyz'
    if n is None:
        n = len(table)
    result = 0
    for char in string:
        result = result * n + table.index(char)
    return result


# ---------------------------------------------------------------------------
# time_seconds — yt-dlp utility (localtime offset helper), not in youtube-dl
# ---------------------------------------------------------------------------

def _time_seconds(**kwargs):
    """Return current UNIX timestamp with optional hour/minute/second offset."""
    t = time.time()
    for unit, secs in (('hours', 3600), ('minutes', 60), ('seconds', 1)):
        t += kwargs.get(unit, 0) * secs
    return t


# ---------------------------------------------------------------------------
# AbemaTV licence urllib handler
#
# yt-dlp architecture:  RequestHandler plugin — registered via
#                         _downloader._request_director.add_handler(...)
#
# youtube-dl architecture: urllib BaseHandler subclass — registered via
#                         opener.add_handler(...)  (on the YoutubeDL opener)
#
# The `abematv-license://` scheme is embedded inside HLS manifests as an
# EXT-X-KEY URI.  When the HLS downloader fetches those URIs it goes through
# the urllib opener, so installing a custom BaseHandler that handles the
# "abematv-license" scheme is the correct integration point.
# ---------------------------------------------------------------------------

class _AbemaTVLicenseHandler(compat_urllib_request.BaseHandler):
    """
    Custom urllib handler for the ``abematv-license://`` URI scheme.

    The HLS manifests served by Abema TV embed licence ticket URIs of the form:
        abematv-license://<ticket>
    This handler intercepts those requests, fetches the decryption key from
    Abema's licence endpoint, performs AES-ECB decryption, and returns the
    raw key bytes as a fake HTTP response so the HLS downloader can use them
    transparently.
    """

    handler_order = 499  # run before default HTTP handlers

    _STRTABLE = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    _HKEY = b'3AF0298C219469522A313570E8583005A642E73EDD58E3EA2FB7339D3DF1597E'

    def __init__(self, ie):
        # ie — the AbemaTVIE instance; stored so we can call its helpers
        self._ie = ie

    # urllib calls <scheme>_open for each scheme it encounters
    def abematv_license_open(self, request):
        url = request.get_full_url()
        ticket = compat_urllib_parse_urlparse(url).netloc

        try:
            key_bytes = self._get_videokey_from_ticket(ticket)
        except (ExtractorError, IndexError, KeyError, TypeError) as e:
            raise compat_urllib_error.URLError(
                'AbemaTV licence error: %s' % e)

        # Wrap raw bytes in a fake addinfourl that works like a real response
        import io
        response = compat_urllib_request.addinfourl(
            io.BytesIO(key_bytes), {}, url, 200)
        # Python 2/3 compat — some urllib versions expect msg attribute
        response.msg = 'OK'
        return response

    def _get_videokey_from_ticket(self, ticket):
        ie = self._ie
        verbose = ie.get_param('verbose', False)
        media_token = ie._get_media_token(to_show=verbose)

        license_response = ie._download_json(
            'https://license.abema.io/abematv-hls', None,
            note='Requesting playback license' if verbose else False,
            query={'t': media_token},
            data=json.dumps({
                'kv': 'a',
                'lt': ticket,
            }).encode('utf-8'),
            headers={'Content-Type': 'application/json'})

        # Decode the base-58 encoded key
        res = _decode_base_n(license_response['k'], table=self._STRTABLE)
        # Convert large integer to 16 big-endian bytes
        encvideokey = []
        for shift in range(120, -8, -8):
            encvideokey.append((res >> shift) & 0xFF)

        # Derive the per-content HMAC key
        h = hmac.new(
            binascii.unhexlify(self._HKEY),
            (license_response['cid'] + ie._DEVICE_ID).encode('utf-8'),
            digestmod=hashlib.sha256)
        enckey = list(h.digest())

        return bytes(_aes_ecb_decrypt(encvideokey, enckey))


# ---------------------------------------------------------------------------
# Base IE
# ---------------------------------------------------------------------------

class AbemaTVBaseIE(InfoExtractor):
    _NETRC_MACHINE = 'abematv'

    # Class-level token cache — shared across all instances (one per session)
    _USERTOKEN = None
    _DEVICE_ID = None
    _MEDIATOKEN = None

    # HMAC secret used by _generate_aks()
    _SECRETKEY = (
        b'v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4h'
        b'Emcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe'
    )

    # Track whether the licence handler has been installed for this session
    _LICENSE_HANDLER_INSTALLED = False

    @classmethod
    def _generate_aks(cls, deviceid):
        """Generate the applicationKeySecret for device registration."""
        deviceid = deviceid.encode('utf-8')
        # Round up to the start of the next hour
        ts_1hour = int((_time_seconds() // 3600 + 1) * 3600)
        time_struct = time.gmtime(ts_1hour)
        ts_1hour_str = compat_str(ts_1hour).encode('utf-8')

        tmp = [None]  # mutable container for nonlocal-like behaviour (Py2 compat)

        def mix_once(nonce):
            h = hmac.new(cls._SECRETKEY, digestmod=hashlib.sha256)
            h.update(nonce)
            tmp[0] = h.digest()

        def mix_tmp(count):
            for _ in range(count):
                mix_once(tmp[0])

        def mix_twist(nonce):
            mix_once(base64.urlsafe_b64encode(tmp[0]).rstrip(b'=') + nonce)

        mix_once(cls._SECRETKEY)
        mix_tmp(time_struct.tm_mon)
        mix_twist(deviceid)
        mix_tmp(time_struct.tm_mday % 5)
        mix_twist(ts_1hour_str)
        mix_tmp(time_struct.tm_hour % 5)

        return base64.urlsafe_b64encode(tmp[0]).rstrip(b'=').decode('utf-8')

    def _install_license_handler(self):
        """
        Register the AbemaTV licence URL handler with youtube-dl's urllib opener.

        This must be called before any HLS download that may encounter
        abematv-license:// URIs.  It is idempotent — calling it multiple times
        has no effect.
        """
        if AbemaTVBaseIE._LICENSE_HANDLER_INSTALLED:
            return
        handler = _AbemaTVLicenseHandler(self)
        self._downloader._opener.add_handler(handler)
        AbemaTVBaseIE._LICENSE_HANDLER_INSTALLED = True

    def _get_device_token(self):
        """
        Obtain (and cache) the anonymous device user token.

        On the first call this:
          1. Installs the abematv-license:// URL handler.
          2. Generates a fresh UUID device ID.
          3. Registers the device with Abema's API to get an anonymous JWT.

        Subsequent calls return the cached token immediately.
        """
        if AbemaTVBaseIE._USERTOKEN:
            return AbemaTVBaseIE._USERTOKEN

        # Install the licence URL handler before any network activity
        self._install_license_handler()

        AbemaTVBaseIE._DEVICE_ID = compat_str(uuid.uuid4())
        aks = self._generate_aks(AbemaTVBaseIE._DEVICE_ID)

        user_data = self._download_json(
            'https://api.abema.io/v1/users', None,
            note='Authorizing',
            data=json.dumps({
                'deviceId': AbemaTVBaseIE._DEVICE_ID,
                'applicationKeySecret': aks,
            }).encode('utf-8'),
            headers={'Content-Type': 'application/json'})

        AbemaTVBaseIE._USERTOKEN = user_data['token']
        return AbemaTVBaseIE._USERTOKEN

    def _get_media_token(self, invalidate=False, to_show=True):
        """
        Fetch (and cache) the short-lived media token required before every
        licence request.  Pass ``invalidate=True`` to force a refresh.
        """
        if not invalidate and AbemaTVBaseIE._MEDIATOKEN:
            return AbemaTVBaseIE._MEDIATOKEN

        note = 'Fetching media token' if to_show else False
        AbemaTVBaseIE._MEDIATOKEN = self._download_json(
            'https://api.abema.io/v1/media/token', None,
            note=note,
            query={
                'osName': 'android',
                'osVersion': '6.0.1',
                'osLang': 'ja_JP',
                'osTimezone': 'Asia/Tokyo',
                'appId': 'tv.abema',
                'appVersion': '3.27.1',
            },
            headers={
                'Authorization': 'bearer ' + self._get_device_token(),
            })['token']

        return AbemaTVBaseIE._MEDIATOKEN

    def _perform_login(self, username, password):
        """Authenticate with Abema TV using email/password or user-ID/password."""
        self._get_device_token()

        if '@' in username:
            ep, method = 'user/email', 'email'
        else:
            ep, method = 'oneTimePassword', 'userId'

        login_response = self._download_json(
            'https://api.abema.io/v1/auth/%s' % ep, None,
            note='Logging in',
            data=json.dumps({
                method: username,
                'password': password,
            }).encode('utf-8'),
            headers={
                'Authorization': 'bearer ' + self._get_device_token(),
                'Origin': 'https://abema.tv',
                'Referer': 'https://abema.tv/',
                'Content-Type': 'application/json',
            })

        AbemaTVBaseIE._USERTOKEN = login_response['token']
        self._get_media_token(invalidate=True)

    def _call_api(self, endpoint, video_id, query=None, note='Downloading JSON metadata'):
        return self._download_json(
            'https://api.abema.io/%s' % endpoint, video_id,
            query=query or {},
            note=note,
            headers={
                'Authorization': 'bearer ' + self._get_device_token(),
            })

    def _extract_breadcrumb_list(self, webpage, video_id):
        """
        Parse the JSON-LD BreadcrumbList embedded in the page to extract
        the series and episode titles.
        """
        for jld_match in re.finditer(
                r'(?is)</span></li></ul><script[^>]+type=(["\']?)application/ld\+json\1[^>]*>(?P<json_ld>.+?)</script>',
                webpage):
            jsonld = self._parse_json(jld_match.group('json_ld'), video_id, fatal=False)
            if not jsonld or jsonld.get('@type') != 'BreadcrumbList':
                continue
            items = []
            for element in jsonld.get('itemListElement') or []:
                name = try_get(element, lambda x: x['name'])
                if name:
                    items.append(compat_str(name))
            if items:
                return items
        return []


# ---------------------------------------------------------------------------
# Main episode / channel IE
# ---------------------------------------------------------------------------

class AbemaTVIE(AbemaTVBaseIE):
    IE_NAME = 'abematv'
    IE_DESC = 'AbemaTV'
    _VALID_URL = r'https?://abema\.tv/(?P<type>now-on-air|video/episode|channels/.+?/slots)/(?P<id>[^?/]+)'

    _TESTS = [{
        'url': 'https://abema.tv/video/episode/194-25_s2_p1',
        'info_dict': {
            'id': '194-25_s2_p1',
            'ext': 'mp4',
            'title': '第1話 「チーズケーキ」　「モーニング再び」',
            'series': '異世界食堂２',
            'season': 'シーズン2',
            'season_number': 2,
            'episode': '第1話 「チーズケーキ」　「モーニング再び」',
            'episode_number': 1,
        },
        'skip': 'expired',
    }, {
        'url': 'https://abema.tv/channels/anime-live2/slots/E8tvAnMJ7a9a5d',
        'info_dict': {
            'id': 'E8tvAnMJ7a9a5d',
            'ext': 'mp4',
            'title': 'ゆるキャン△ SEASON２ 全話一挙【無料ビデオ72時間】',
            'series': 'ゆるキャン△ SEASON２',
            'episode': 'ゆるキャン△ SEASON２ 全話一挙【無料ビデオ72時間】',
            'season_number': 2,
            'episode_number': 1,
        },
        'skip': 'expired',
    }, {
        'url': 'https://abema.tv/now-on-air/abema-anime',
        'info_dict': {
            'id': 'abema-anime',
            'ext': 'mp4',
            'is_live': True,
        },
        'skip': 'Live stream — use Streamlink for reliable capture',
    }]

    # Timetable cache (up to ~5 MiB) — fetched lazily for now-on-air lookups
    _TIMETABLE = None

    def _real_extract(self, url):
        # Ensure the licence handler and device token are ready before we touch
        # anything network-related (the handler must be in place before the HLS
        # downloader encounters abematv-license:// URIs).
        self._get_device_token()

        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        video_type = mobj.group('type').split('/')[-1]  # 'now-on-air' | 'episode' | 'slots'

        auth_headers = {
            'Authorization': 'Bearer ' + self._get_device_token(),
        }

        webpage = self._download_webpage(url, video_id)

        canonical_url = self._search_regex(
            r'<link\s+rel="canonical"\s*href="(.+?)"',
            webpage, 'canonical URL', default=url)

        info = self._search_json_ld(webpage, video_id, default={})

        # ------------------------------------------------------------------
        # Title extraction — three fallback layers
        # ------------------------------------------------------------------
        title = self._search_regex(
            r'<span\s*class="[^"]*EpisodeTitleBlock__title[^"]*">(.+?)</span>',
            webpage, 'title', default=None)

        if not title:
            # Try JSON-LD caption adjacent to thumbnail
            for jld_match in re.finditer(
                    r'(?is)<span\s*class="com-m-Thumbnail__image">(?:</span>)?'
                    r'<script[^>]+type=(["\']?)application/ld\+json\1[^>]*>'
                    r'(?P<json_ld>.+?)</script>',
                    webpage):
                jsonld = self._parse_json(jld_match.group('json_ld'), video_id, fatal=False)
                if jsonld:
                    title = jsonld.get('caption')
                    break

        if not title and video_type == 'now-on-air':
            # Fetch the full timetable once per session and search for the
            # currently-airing programme on this channel
            if not self._TIMETABLE:
                self._TIMETABLE = self._download_json(
                    'https://api.abema.io/v1/timetable/dataSet?debug=false',
                    video_id, headers=auth_headers)
            # Abema uses JST (UTC+9)
            now = _time_seconds(hours=9)
            for slot in (self._TIMETABLE.get('slots') or []):
                if slot.get('channelId') != video_id:
                    continue
                if slot['startAt'] <= now < slot['endAt']:
                    title = slot.get('title')
                    break

        # ------------------------------------------------------------------
        # Breadcrumb (series / episode hierarchy)
        # ------------------------------------------------------------------
        breadcrumb = self._extract_breadcrumb_list(webpage, video_id)
        if breadcrumb:
            # Structure: Home > Genre > Series > Episode
            info['series'] = breadcrumb[-2] if len(breadcrumb) >= 2 else None
            info['episode'] = breadcrumb[-1]
            if not title:
                title = info['episode']

        # ------------------------------------------------------------------
        # Description
        # ------------------------------------------------------------------
        description = self._html_search_regex(
            (r'<p\s+class="com-video-EpisodeDetailsBlock__content">'
             r'<span\s+class="[^"]+">(.+?)</span></p><div',
             r'<span\s+class="[^"]*SlotSummary[^"]*">(.+?)</span></div><div'),
            webpage, 'description', default=None, group=1)
        if not description:
            og_desc = self._html_search_meta(
                ('description', 'og:description', 'twitter:description'), webpage)
            if og_desc:
                description = re.sub(
                    r'''(?sx)
                        ^(.+?)(?:
                            アニメの動画を無料で見るならABEMA！|
                            等、.+
                        )?$
                    ''', r'\1', og_desc).strip()

        # ------------------------------------------------------------------
        # Season / episode numbers from canonical URL (e.g. _s2_p31)
        # ------------------------------------------------------------------
        mobj = re.search(r's(\d+)_p(\d+)$', canonical_url)
        if mobj:
            seri = int_or_none(mobj.group(1))
            epis = int_or_none(mobj.group(2))
            if seri is not None and seri < 100:
                info['season_number'] = seri
            if epis is not None and epis < 2000:
                info['episode_number'] = epis

        # ------------------------------------------------------------------
        # API-type-specific logic: find the m3u8 URL
        # ------------------------------------------------------------------
        is_live = False
        m3u8_url = None

        if video_type == 'now-on-air':
            is_live = True
            channel_url = 'https://api.abema.io/v1/channels'
            if video_id == 'news-global':
                channel_url = update_url_query(channel_url, {'division': '1'})
            onair_channels = self._download_json(
                channel_url, video_id, headers=auth_headers)
            for ch in (onair_channels.get('channels') or []):
                if ch.get('id') == video_id:
                    m3u8_url = try_get(ch, lambda x: x['playback']['hls'])
                    break
            if not m3u8_url:
                raise ExtractorError(
                    'Cannot find on-air channel: %s' % video_id, expected=True)

        elif video_type == 'episode':
            api_response = self._download_json(
                'https://api.abema.io/v1/video/programs/%s' % video_id,
                video_id, note='Checking playability', headers=auth_headers)

            # Check whether the episode is free
            is_free = try_get(api_response, lambda x: x['label']['free'])
            if not is_free:
                self.report_warning('This is a premium-only stream')

            # Enrich info dict from API (overrides JSON-LD values where present)
            series = try_get(api_response, lambda x: x['series']['title'])
            season = try_get(api_response, lambda x: x['season']['name'])
            season_num = try_get(api_response, lambda x: x['season']['sequence'])
            ep_num = try_get(api_response, lambda x: x['episode']['number'])
            ep_title = try_get(api_response, lambda x: x['episode']['title'])
            ep_content = try_get(api_response, lambda x: x['episode']['content'])

            if series:
                info['series'] = series
            if season:
                info['season'] = season
            if season_num is not None:
                info['season_number'] = int_or_none(season_num)
            if ep_num is not None:
                info['episode_number'] = int_or_none(ep_num)
            if ep_title and not title:
                title = ep_title
            if ep_content and not description:
                description = ep_content

            m3u8_url = (
                'https://vod-abematv.akamaized.net/program/%s/playlist.m3u8'
                % video_id)

        elif video_type == 'slots':
            api_response = self._download_json(
                'https://api.abema.io/v1/media/slots/%s' % video_id,
                video_id, note='Checking playability', headers=auth_headers)

            timeshift_free = try_get(
                api_response, lambda x: x['slot']['flags']['timeshiftFree'],
                bool)
            if not timeshift_free:
                self.report_warning('This is a premium-only stream')

            m3u8_url = (
                'https://vod-abematv.akamaized.net/slot/%s/playlist.m3u8'
                % video_id)
        else:
            raise ExtractorError('Unrecognised video type: %s' % video_type)

        # ------------------------------------------------------------------
        # Live-stream warning
        # ------------------------------------------------------------------
        if is_live:
            self.report_warning(
                'This is a livestream; youtube-dl does not support downloading '
                'natively. FFmpeg cannot handle AbemaTV m3u8 manifests reliably. '
                'Consider using Streamlink: https://github.com/streamlink/streamlink')

        # The Akamai CDN that serves AbemaTV HLS manifests enforces two checks:
        #   1. A valid Bearer token matching the registered device session.
        #   2. A User-Agent consistent with the Android app context used during
        #      device registration (osName=android, appId=tv.abema).
        #      youtube-dl's default desktop Chrome UA causes a 403 here.
        m3u8_headers = {
            'Authorization': 'Bearer ' + self._get_device_token(),
            'User-Agent': (
                'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/88.0.4324.96 Mobile Safari/537.36 (compatible; abema-android/3.27.1)'
            ),
            'Origin': 'https://abema.tv',
            'Referer': 'https://abema.tv/',
        }

        # ---- DEBUG: dump the exact headers and URL going to Akamai --------
        # Remove this block once the 403 is resolved.
        sys.stderr.write('[abematv-debug] m3u8_url  = %s\n' % m3u8_url)
        sys.stderr.write('[abematv-debug] m3u8_headers:\n')
        for _k, _v in sorted(m3u8_headers.items()):
            sys.stderr.write('[abematv-debug]   %s: %s\n' % (_k, _v))
        sys.stderr.flush()
        # ---- END DEBUG ----------------------------------------------------

        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, ext='mp4', entry_protocol='m3u8_native',
            m3u8_id='hls', live=is_live, headers=m3u8_headers)
        self._sort_formats(formats)

        # ------------------------------------------------------------------
        # Thumbnail
        # ------------------------------------------------------------------
        thumbnail = self._og_search_thumbnail(webpage, default=None)
        # Strip query parameters (Abema signs thumbnails; strip to get stable URL)
        if thumbnail:
            thumbnail = thumbnail.split('?')[0]

        info.update({
            'id': video_id,
            'title': title or video_id,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
            'is_live': is_live,
        })
        return info


# ---------------------------------------------------------------------------
# Title (series / playlist) IE
# ---------------------------------------------------------------------------

class AbemaTVTitleIE(AbemaTVBaseIE):
    IE_NAME = 'abematv:title'
    IE_DESC = 'AbemaTV series'
    _VALID_URL = (
        r'https?://abema\.tv/video/title/(?P<id>[^?/#]+)'
        r'/?(?:\?(?:[^#]+&)?s=(?P<season>[^&#]+))?'
    )
    _PAGE_SIZE = 25

    _TESTS = [{
        'url': 'https://abema.tv/video/title/90-1887',
        'info_dict': {
            'id': '90-1887',
            'title': 'シャッフルアイランド',
        },
        'playlist_mincount': 2,
    }, {
        'url': 'https://abema.tv/video/title/193-132',
        'info_dict': {
            'id': '193-132',
            'title': '真心が届く~僕とスターのオフィス・ラブ!?~',
        },
        'playlist_mincount': 16,
    }, {
        'url': 'https://abema.tv/video/title/25-1nzan-whrxe',
        'info_dict': {
            'id': '25-1nzan-whrxe',
            'title': 'ソードアート・オンライン',
        },
        'playlist_mincount': 25,
    }, {
        'url': 'https://abema.tv/video/title/26-2mzbynr-cph?s=26-2mzbynr-cph_s40',
        'info_dict': {
            'id': '26-2mzbynr-cph',
            'title': '〈物語〉シリーズ',
        },
        'playlist_count': 59,
    }]

    def _fetch_page(self, playlist_id, series_version, season_id, page):
        query = {
            'seriesVersion': series_version,
            'offset': compat_str(page * self._PAGE_SIZE),
            'order': 'seq',
            'limit': compat_str(self._PAGE_SIZE),
        }
        if season_id:
            query['seasonId'] = season_id

        programs = self._call_api(
            'v1/video/series/%s/programs' % playlist_id,
            playlist_id,
            note='Downloading page %d' % (page + 1),
            query=query)

        for program_id in (try_get(programs, lambda x: x['programs']) or []):
            pid = try_get(program_id, lambda x: x['id'])
            if pid:
                yield self.url_result(
                    'https://abema.tv/video/episode/%s' % pid,
                    ie=AbemaTVIE.ie_key())

    def _entries(self, playlist_id, series_version, season_id):
        return OnDemandPagedList(
            functools.partial(
                self._fetch_page, playlist_id, series_version, season_id),
            self._PAGE_SIZE)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')
        season_id = mobj.group('season')  # may be None

        series_info = self._call_api(
            'v1/video/series/%s' % playlist_id, playlist_id)

        return self.playlist_result(
            self._entries(playlist_id, series_info['version'], season_id),
            playlist_id=playlist_id,
            playlist_title=series_info.get('title'),
            playlist_description=series_info.get('content'))
