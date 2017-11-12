# coding: utf-8
from __future__ import unicode_literals

from uuid import uuid4
import re

from .common import InfoExtractor
from ..utils import (
    compat_str,
    ExtractorError,
    sanitized_Request,
    urlencode_postdata,
)


class ZattooBaseIE(InfoExtractor):

    _NETRC_MACHINE = 'zattoo'
    _HOST_URL = 'https://zattoo.com'

    _login_info = {}

    def _login(self, uuid, session_id):
        (username, password) = self._get_login_info()
        if not username or not password:
            raise ExtractorError(
                'A valid %s account is needed to access this media.' % self._NETRC_MACHINE,
                expected=True)
        login_form = {
            'login': username,
            'password': password,
            'remember': True,
        }
        request = sanitized_Request(
            '%s/zapi/v2/account/login' % self._HOST_URL,
            urlencode_postdata(login_form))
        request.add_header(
            'Referer', '%s/login' % self._HOST_URL)
        request.add_header(
            'Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        request.add_header(
            'Cookie', self._generate_cookie(uuid, session_id))
        response = self._request_webpage(
            request, None, 'Logging in')
        cookie = response.headers.get('Set-Cookie')
        pzuid = self._search_regex(r'pzuid\s*=\s*(.+?);', cookie, 'pzuid')
        data = self._parse_json(response.read(), None)

        return {
            'ppid': data['session']['ppid'],
            'powerhash': data['session']['power_guide_hash'],
            'pzuid': pzuid,
            'uuid': uuid,
            'session_id': session_id
        }

    def _get_app_token_and_version(self):
        host_webpage = self._download_webpage(
            self._HOST_URL, None, 'Downloading %s' % self._HOST_URL)
        app_token = self._html_search_regex(
            r'<script.+window\.appToken\s*=\s*\'(.+)\'', host_webpage, 'app token')
        app_version = self._html_search_regex(
            r'<!--\w+-(.+?)-', host_webpage, 'app version')
        return app_token, app_version

    def _say_hello(self, uuid, app_token, app_version):
        postdata = {
            'client_app_token': app_token,
            'uuid': uuid,
            'lang': 'en',
            'app_version': app_version,
            'format': 'json',
        }
        request = sanitized_Request(
            '%s/zapi/v2/session/hello' % self._HOST_URL,
            urlencode_postdata(postdata))
        response = self._request_webpage(
            request, None, 'Say hello')

        cookie = response.headers.get('Set-Cookie')
        session_id = self._search_regex(
            r'beaker\.session\.id\s*=\s*(.+?);', cookie, 'session id')
        return session_id

    def _generate_cookie(self, uuid, session_id, pzuid=None):
        if not pzuid:
            return 'uuid=%s; beaker.session.id=%s' % (uuid, session_id)
        return 'uuid=%s; beaker.session.id=%s; pzuid=%s' % (uuid, session_id, pzuid)

    def _get_channels_display_cid(self, login_info, video_id):
        data = self._download_json(
            '%s/zapi/v2/cached/channels/%s' % (self._HOST_URL,
                                               login_info['powerhash']),
            video_id,
            'Downloading available channel list',
            query={'details': False})
        display_cid = {}
        for elem in data['channel_groups']:
            for channel in elem['channels']:
                display_cid[channel['display_alias']] = channel['cid']
        return display_cid

    def _extract_cid(self, login_info, video_id, channel_name):
        display_cid = self._get_channels_display_cid(login_info, video_id)
        return display_cid[channel_name]

    def _extract_cid_and_video_info(self, video_id):
        data = self._download_json(
            '%s/zapi/program/details' % self._HOST_URL,
            video_id,
            'Downloading video information',
            query={
                'program_id': video_id,
                'complete': True
            })

        info_dict = {
            'id': video_id,
            'title': data['program']['title'],
            'description': data['program'].get('description'),
            'thumbnail': data['program'].get('image_url')
        }
        cid = data['program']['cid']
        return cid, info_dict

    def _add_hls_format_information(self, formats):
        hls_formats = list(filter(
            lambda f: f.get('format_id').startswith('hls'), formats))
        dash_formats = list(filter(
            lambda f: f.get('format_id').startswith('dash') and
            f.get('acodec') == 'none', formats))
        if len(hls_formats) == len(dash_formats):
            for hls, dash in zip(hls_formats, dash_formats):
                hls['ext'] = dash.get('ext')
                hls['fps'] = dash.get('fps')
                hls['tbr'] = dash.get('tbr')
                hls['width'] = dash.get('width')
                hls['height'] = dash.get('height')

    def _extract_formats(self, cid, video_id, is_live=False):
        postdata = {
            'stream_type': 'dash',
            'https_watch_urls': True,
        }
        url = '%s/zapi/watch/recall/%s/%s' % (self._HOST_URL, cid, video_id)

        if is_live:
            postdata.update({'timeshift': 10800})
            url = '%s/zapi/watch/live/%s' % (self._HOST_URL, cid)

        data = self._download_json(
            sanitized_Request(url, urlencode_postdata(postdata)),
            video_id, 'Downloading dash formats')

        formats = []
        quality = 'hd'
        for elem in data['stream']['watch_urls']:
            if elem.get('audio_channel') == 'A':
                formats.extend(
                    self._extract_mpd_formats(
                        elem['url'], video_id,
                        mpd_id='dash-%s' % quality, fatal=False))
                quality = 'sd'

        postdata.update({'stream_type': 'hls'})
        if is_live:
            postdata.update({'timeshift': 10800})
        request = sanitized_Request(
            url, urlencode_postdata(postdata))
        data = self._download_json(
            request, video_id, 'Downloading hls formats')
        quality = 'hd'
        for elem in data['stream']['watch_urls']:
            if elem.get('audio_channel') == 'A':
                formats.extend(
                    self._extract_m3u8_formats(
                        elem['url'], video_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id='hls-%s' % quality, fatal=False))
                quality = 'sd'

        self._add_hls_format_information(formats)
        self._sort_formats(formats)
        return formats

    def _real_initialize(self):
        uuid = compat_str(uuid4())
        app_token, app_version = self._get_app_token_and_version()
        session_id = self._say_hello(uuid, app_token, app_version)
        self._login_info = self._login(uuid, session_id)

    def _extract_video(self, channel_name, video_id, is_live=False):
        if is_live:
            cid = self._extract_cid(self._login_info, video_id, channel_name)
            info_dict = {
                'id': channel_name,
                'title': self._live_title(channel_name),
                'is_live': True,
            }
        else:
            cid, info_dict = self._extract_cid_and_video_info(video_id)
        formats = self._extract_formats(
            cid, video_id, is_live=is_live)
        info_dict['formats'] = formats
        return info_dict


class QuicklineBaseIE(ZattooBaseIE):
    _NETRC_MACHINE = 'quickline'
    _HOST_URL = 'https://mobiltv.quickline.com'


class QuicklineIE(QuicklineBaseIE):
    _VALID_URL = r'https?://(?:www\.)?mobiltv\.quickline\.com/watch/(?P<channel>[^/]+)/(?P<id>[0-9]+)'

    def _real_extract(self, url):
        channel_name, video_id = re.match(self._VALID_URL, url).groups()
        return self._extract_video(channel_name, video_id)


class QuicklineLiveIE(QuicklineBaseIE):
    _VALID_URL = r'https?://(?:www\.)?mobiltv\.quickline\.com/watch/(?P<id>[^/]+)$'

    def _real_extract(self, url):
        channel_name = video_id = self._match_id(url)
        return self._extract_video(channel_name, video_id, is_live=True)


class ZattooIE(ZattooBaseIE):
    _VALID_URL = r'https?://(?:www\.)?zattoo\.com/watch/(?P<channel>[^/]+)/(?P<id>[0-9]+)'

    # Since videos are only available for 7 days, we cannot have detailed tests.
    _TEST = {
        'url': 'https://zattoo.com/watch/prosieben/130671867-maze-runner-die-auserwaehlten-in-der-brandwueste',
        'only_matching': True,
    }

    def _real_extract(self, url):
        channel_name, video_id = re.match(self._VALID_URL, url).groups()
        return self._extract_video(channel_name, video_id)


class ZattooLiveIE(ZattooBaseIE):
    _VALID_URL = r'https?://(?:www\.)?zattoo\.com/watch/(?P<id>[^/]+)$'

    _TEST = {
        'url': 'https://zattoo.com/watch/srf1',
        'only_matching': True,
    }

    def _real_extract(self, url):
        channel_name = video_id = self._match_id(url)
        return self._extract_video(channel_name, video_id, is_live=True)
