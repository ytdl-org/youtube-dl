# coding: utf-8
from __future__ import unicode_literals

import uuid
import re

from .common import InfoExtractor
from ..utils import (
    compat_str,
    ExtractorError,
    sanitized_Request,
    urlencode_postdata,
    urljoin,
)


class ZattooBaseIE(InfoExtractor):

    _NETRC_MACHINE = 'zattoo'
    _HOST_URL = 'https://zattoo.com/'

    def _login(self, uuid, session_id, video_id):
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
            urljoin(self._HOST_URL, '/zapi/v2/account/login'),
            urlencode_postdata(login_form))
        request.add_header(
            'Referer', urljoin(self._HOST_URL, '/login'))
        request.add_header(
            'Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        request.add_header(
            'Cookie', self._generate_cookie(uuid, session_id))
        response = self._request_webpage(
            request, video_id, 'Logging in as %s' % login_form['login'])
        cookie = response.headers.get('Set-Cookie')
        pzuid = self._search_regex(r'pzuid\s*=\s*(.+?);', cookie, 'pzuid')
        data = self._parse_json(
            response.read(), video_id)

        return {
            'ppid': data['session']['ppid'],
            'powerhash': data['session']['power_guide_hash'],
            'pzuid': pzuid,
            'uuid': uuid,
            'session_id': session_id
        }

    def _get_app_token_and_version(self, video_id):
        host_webpage = self._download_webpage(
            self._HOST_URL, video_id)
        app_token = self._html_search_regex(
            r'<script.+window\.appToken\s*=\s*\'(.+)\'', host_webpage, 'app token')
        app_version = self._html_search_regex(
            r'<!--\w+-(.+?)-', host_webpage, 'app version')
        return app_token, app_version

    def _say_hello(self, video_id, uuid, app_token, app_version):
        postdata = {
            'client_app_token': app_token,
            'uuid': uuid,
            'lang': 'en',
            'app_version': app_version,
            'format': 'json',
        }
        request = sanitized_Request(
            urljoin(self._HOST_URL, '/zapi/v2/session/hello'),
            urlencode_postdata(postdata))
        response = self._request_webpage(
            request, video_id, 'Say hello')

        cookie = response.headers.get('Set-Cookie')
        session_id = self._search_regex(
            r'beaker\.session\.id\s*=\s*(.+?);', cookie, 'session id')
        return session_id

    def _generate_cookie(self, uuid, session_id, pzuid=None):
        if not pzuid:
            return 'uuid=%s; beaker.session.id=%s' % (uuid, session_id)
        return 'uuid=%s; beaker.session.id=%s; pzuid=%s' % (uuid, session_id, pzuid)

    def _get_channels_display_cid(self, login_info, video_id):
        request_url = urljoin(self._HOST_URL,
                              '/zapi/v2/cached/channels/%s&details=False' % login_info['powerhash'])
        data = self._download_json(
            request_url, video_id, 'Downloading available channel list')
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
            urljoin(self._HOST_URL,
                    '/zapi/program/details?program_id=%s&complete=True' % video_id),
            video_id, 'Downloading video information')

        info_dict = {
            'id': video_id,
            'title': data['program']['title'],
            'description': data['program'].get('description'),
            'thumbnail': data['program'].get('image_url')
        }
        cid = data['program']['cid']
        return cid, info_dict

    def _store_dash_format_properties(self, dash_formats, store_list):
        for form in dash_formats:
            if form.get('format_note') == 'DASH video':
                store_list.append(
                    {
                        'ext': form.get('ext'),
                        'width': form.get('width'),
                        'height': form.get('height'),
                        'tbr': form.get('tbr'),
                        'fps': form.get('fps'),
                    }
                )

    def _add_stored_information(self, store_list, hls_formats, i_dash):
        for form in hls_formats:
            if i_dash < len(store_list):
                form.update(store_list[i_dash])
                i_dash += 1
        return i_dash

    def _extract_formats(self, cid, video_id, is_live=False):
        postdata = {
            'stream_type': 'dash',
            'https_watch_urls': True,
        }
        url = urljoin(self._HOST_URL, '/zapi/watch/recall/%s/%s' %
                      (cid, video_id))

        if is_live:
            postdata.update({'timeshift': 10800})
            url = urljoin(self._HOST_URL, '/zapi/watch/live/%s' % cid)

        request = sanitized_Request(
            url, urlencode_postdata(postdata))

        data = self._download_json(
            request, video_id, 'Downloading dash formats')

        formats = []
        format_info_list = []
        quality = 'hd'
        for elem in data['stream']['watch_urls']:
            if elem.get('audio_channel') == 'A':
                dash_formats = self._extract_mpd_formats(
                    elem['url'], video_id, mpd_id='dash-%s' % quality, fatal=False)

                self._store_dash_format_properties(
                    dash_formats, format_info_list)
                formats.extend(dash_formats)
                quality = 'sd'

        postdata.update({'stream_type': 'hls'})
        if is_live:
            postdata.update({'timeshift': 10800})
        request = sanitized_Request(
            url, urlencode_postdata(postdata))
        data = self._download_json(
            request, video_id, 'Downloading hls formats')
        quality = 'hd'
        i_dash = 0
        for elem in data['stream']['watch_urls']:
            if elem.get('audio_channel') == 'A':
                hls_formats = self._extract_m3u8_formats(
                    elem['url'], video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls-%s' % quality, fatal=False)
                i_dash = self._add_stored_information(
                    format_info_list, hls_formats, i_dash)
                formats.extend(hls_formats)
                quality = 'sd'

        self._sort_formats(formats)
        return formats

    def _generate_uuid(self):
        return compat_str(uuid.uuid4())

    def _extract_video(self, channel_name, video_id, is_live=False):
        uuid = self._generate_uuid()
        app_token, app_version = self._get_app_token_and_version(video_id)
        session_id = self._say_hello(video_id, uuid, app_token, app_version)
        login_info = self._login(uuid, session_id, video_id)
        if is_live:
            cid = self._extract_cid(login_info, video_id, channel_name)
            info_dict = {
                'id': channel_name,
                'title': '%s-%s' % (channel_name, 'live'),
                'is_live': True,
            }
        else:
            cid, info_dict = self._extract_cid_and_video_info(video_id)
        formats = self._extract_formats(
            cid, video_id, is_live=is_live)
        info_dict.update({'formats': formats})
        return info_dict


class QuicklineBaseIE(ZattooBaseIE):
    _NETRC_MACHINE = 'quickline'
    _HOST_URL = 'https://mobiltv.quickline.com/'


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
