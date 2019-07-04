from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from .gigya import GigyaBaseIE
from ..compat import compat_HTTPError
from ..utils import (
    ExtractorError,
    strip_or_none,
    float_or_none,
    int_or_none,
    merge_dicts,
    parse_iso8601,
)


class CanvasIE(InfoExtractor):
    _VALID_URL = r'https?://mediazone\.vrt\.be/api/v1/(?P<site_id>canvas|een|ketnet|vrt(?:video|nieuws)|sporza)/assets/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://mediazone.vrt.be/api/v1/ketnet/assets/md-ast-4ac54990-ce66-4d00-a8ca-9eac86f4c475',
        'md5': '90139b746a0a9bd7bb631283f6e2a64e',
        'info_dict': {
            'id': 'md-ast-4ac54990-ce66-4d00-a8ca-9eac86f4c475',
            'display_id': 'md-ast-4ac54990-ce66-4d00-a8ca-9eac86f4c475',
            'ext': 'flv',
            'title': 'Nachtwacht: De Greystook',
            'description': 'md5:1db3f5dc4c7109c821261e7512975be7',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 1468.03,
        },
        'expected_warnings': ['is not a supported codec', 'Unknown MIME type'],
    }, {
        'url': 'https://mediazone.vrt.be/api/v1/canvas/assets/mz-ast-5e5f90b6-2d72-4c40-82c2-e134f884e93e',
        'only_matching': True,
    }]
    _HLS_ENTRY_PROTOCOLS_MAP = {
        'HLS': 'm3u8_native',
        'HLS_AES': 'm3u8',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        site_id, video_id = mobj.group('site_id'), mobj.group('id')

        data = self._download_json(
            'https://mediazone.vrt.be/api/v1/%s/assets/%s'
            % (site_id, video_id), video_id)

        title = data['title']
        description = data.get('description')

        formats = []
        for target in data['targetUrls']:
            format_url, format_type = target.get('url'), target.get('type')
            if not format_url or not format_type:
                continue
            if format_type in self._HLS_ENTRY_PROTOCOLS_MAP:
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', self._HLS_ENTRY_PROTOCOLS_MAP[format_type],
                    m3u8_id=format_type, fatal=False))
            elif format_type == 'HDS':
                formats.extend(self._extract_f4m_formats(
                    format_url, video_id, f4m_id=format_type, fatal=False))
            elif format_type == 'MPEG_DASH':
                formats.extend(self._extract_mpd_formats(
                    format_url, video_id, mpd_id=format_type, fatal=False))
            elif format_type == 'HSS':
                formats.extend(self._extract_ism_formats(
                    format_url, video_id, ism_id='mss', fatal=False))
            else:
                formats.append({
                    'format_id': format_type,
                    'url': format_url,
                })
        self._sort_formats(formats)

        subtitles = {}
        subtitle_urls = data.get('subtitleUrls')
        if isinstance(subtitle_urls, list):
            for subtitle in subtitle_urls:
                subtitle_url = subtitle.get('url')
                if subtitle_url and subtitle.get('type') == 'CLOSED':
                    subtitles.setdefault('nl', []).append({'url': subtitle_url})

        return {
            'id': video_id,
            'display_id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'duration': float_or_none(data.get('duration'), 1000),
            'thumbnail': data.get('posterImageUrl'),
            'subtitles': subtitles,
        }


class CanvasEenIE(InfoExtractor):
    IE_DESC = 'canvas.be and een.be'
    _VALID_URL = r'https?://(?:www\.)?(?P<site_id>canvas|een)\.be/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://www.canvas.be/video/de-afspraak/najaar-2015/de-afspraak-veilt-voor-de-warmste-week',
        'md5': 'ed66976748d12350b118455979cca293',
        'info_dict': {
            'id': 'mz-ast-5e5f90b6-2d72-4c40-82c2-e134f884e93e',
            'display_id': 'de-afspraak-veilt-voor-de-warmste-week',
            'ext': 'flv',
            'title': 'De afspraak veilt voor de Warmste Week',
            'description': 'md5:24cb860c320dc2be7358e0e5aa317ba6',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 49.02,
        },
        'expected_warnings': ['is not a supported codec'],
    }, {
        # with subtitles
        'url': 'http://www.canvas.be/video/panorama/2016/pieter-0167',
        'info_dict': {
            'id': 'mz-ast-5240ff21-2d30-4101-bba6-92b5ec67c625',
            'display_id': 'pieter-0167',
            'ext': 'mp4',
            'title': 'Pieter 0167',
            'description': 'md5:943cd30f48a5d29ba02c3a104dc4ec4e',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 2553.08,
            'subtitles': {
                'nl': [{
                    'ext': 'vtt',
                }],
            },
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Pagina niet gevonden',
    }, {
        'url': 'https://www.een.be/sorry-voor-alles/herbekijk-sorry-voor-alles',
        'info_dict': {
            'id': 'mz-ast-11a587f8-b921-4266-82e2-0bce3e80d07f',
            'display_id': 'herbekijk-sorry-voor-alles',
            'ext': 'mp4',
            'title': 'Herbekijk Sorry voor alles',
            'description': 'md5:8bb2805df8164e5eb95d6a7a29dc0dd3',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 3788.06,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Episode no longer available',
    }, {
        'url': 'https://www.canvas.be/check-point/najaar-2016/de-politie-uw-vriend',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        site_id, display_id = mobj.group('site_id'), mobj.group('id')

        webpage = self._download_webpage(url, display_id)

        title = strip_or_none(self._search_regex(
            r'<h1[^>]+class="video__body__header__title"[^>]*>(.+?)</h1>',
            webpage, 'title', default=None) or self._og_search_title(
            webpage, default=None))

        video_id = self._html_search_regex(
            r'data-video=(["\'])(?P<id>(?:(?!\1).)+)\1', webpage, 'video id',
            group='id')

        return {
            '_type': 'url_transparent',
            'url': 'https://mediazone.vrt.be/api/v1/%s/assets/%s' % (site_id, video_id),
            'ie_key': CanvasIE.ie_key(),
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': self._og_search_description(webpage),
        }


class VrtNUIE(GigyaBaseIE):
    IE_DESC = 'VrtNU.be'
    _VALID_URL = r'https?://(?:www\.)?vrt\.be/(?P<site_id>vrtnu)/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.vrt.be/vrtnu/a-z/postbus-x/1/postbus-x-s1a1/',
        'info_dict': {
            'id': 'pbs-pub-2e2d8c27-df26-45c9-9dc6-90c78153044d$vid-90c932b1-e21d-4fb8-99b1-db7b49cf74de',
            'ext': 'flv',
            'title': 'De zwarte weduwe',
            'description': 'md5:d90c21dced7db869a85db89a623998d4',
            'duration': 1457.04,
            'thumbnail': r're:^https?://.*\.jpg$',
            'season': '1',
            'season_number': 1,
            'episode_number': 1,
        },
        'skip': 'This video is only available for registered users'
    }]
    _NETRC_MACHINE = 'vrtnu'
    _APIKEY = '3_0Z2HujMtiWq_pkAjgnS2Md2E11a1AwZjYiBETtwNE-EoEHDINgtnvcAOpNgmrVGy'
    _CONTEXT_ID = 'R3595707040'

    def _real_initialize(self):
        self._login()

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        auth_data = {
            'APIKey': self._APIKEY,
            'targetEnv': 'jssdk',
            'loginID': username,
            'password': password,
            'authMode': 'cookie',
        }

        auth_info = self._gigya_login(auth_data)

        # Sometimes authentication fails for no good reason, retry
        login_attempt = 1
        while login_attempt <= 3:
            try:
                # When requesting a token, no actual token is returned, but the
                # necessary cookies are set.
                self._request_webpage(
                    'https://token.vrt.be',
                    None, note='Requesting a token', errnote='Could not get a token',
                    headers={
                        'Content-Type': 'application/json',
                        'Referer': 'https://www.vrt.be/vrtnu/',
                    },
                    data=json.dumps({
                        'uid': auth_info['UID'],
                        'uidsig': auth_info['UIDSignature'],
                        'ts': auth_info['signatureTimestamp'],
                        'email': auth_info['profile']['email'],
                    }).encode('utf-8'))
            except ExtractorError as e:
                if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                    login_attempt += 1
                    self.report_warning('Authentication failed')
                    self._sleep(1, None, msg_template='Waiting for %(timeout)s seconds before trying again')
                else:
                    raise e
            else:
                break

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage, urlh = self._download_webpage_handle(url, display_id)

        info = self._search_json_ld(webpage, display_id, default={})

        # title is optional here since it may be extracted by extractor
        # that is delegated from here
        title = strip_or_none(self._html_search_regex(
            r'(?ms)<h1 class="content__heading">(.+?)</h1>',
            webpage, 'title', default=None))

        description = self._html_search_regex(
            r'(?ms)<div class="content__description">(.+?)</div>',
            webpage, 'description', default=None)

        season = self._html_search_regex(
            [r'''(?xms)<div\ class="tabs__tab\ tabs__tab--active">\s*
                    <span>seizoen\ (.+?)</span>\s*
                </div>''',
             r'<option value="seizoen (\d{1,3})" data-href="[^"]+?" selected>'],
            webpage, 'season', default=None)

        season_number = int_or_none(season)

        episode_number = int_or_none(self._html_search_regex(
            r'''(?xms)<div\ class="content__episode">\s*
                    <abbr\ title="aflevering">afl</abbr>\s*<span>(\d+)</span>
                </div>''',
            webpage, 'episode_number', default=None))

        release_date = parse_iso8601(self._html_search_regex(
            r'(?ms)<div class="content__broadcastdate">\s*<time\ datetime="(.+?)"',
            webpage, 'release_date', default=None))

        # If there's a ? or a # in the URL, remove them and everything after
        clean_url = urlh.geturl().split('?')[0].split('#')[0].strip('/')
        securevideo_url = clean_url + '.mssecurevideo.json'

        try:
            video = self._download_json(securevideo_url, display_id)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                self.raise_login_required()
            raise

        # We are dealing with a '../<show>.relevant' URL
        redirect_url = video.get('url')
        if redirect_url:
            return self.url_result(self._proto_relative_url(redirect_url, 'https:'))

        # There is only one entry, but with an unknown key, so just get
        # the first one
        video_id = list(video.values())[0].get('videoid')

        return merge_dicts(info, {
            '_type': 'url_transparent',
            'url': 'https://mediazone.vrt.be/api/v1/vrtvideo/assets/%s' % video_id,
            'ie_key': CanvasIE.ie_key(),
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'season': season,
            'season_number': season_number,
            'episode_number': episode_number,
            'release_date': release_date,
        })
