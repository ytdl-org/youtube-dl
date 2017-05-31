from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_duration,
    try_get,
    unified_timestamp,
    urlencode_postdata,
)


class MedialaanIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.|nieuws\.)?
                        (?:
                            (?P<site_id>vtm|q2|vtmkzoom)\.be/
                            (?:
                                video(?:/[^/]+/id/|/?\?.*?\baid=)|
                                (?:[^/]+/)*
                            )
                        )
                        (?P<id>[^/?#&]+)
                    '''
    _NETRC_MACHINE = 'medialaan'
    _APIKEY = '3_HZ0FtkMW_gOyKlqQzW5_0FHRC7Nd5XpXJZcDdXY4pk5eES2ZWmejRW5egwVm4ug-'
    _SITE_TO_APP_ID = {
        'vtm': 'vtm_watch',
        'q2': 'q2',
        'vtmkzoom': 'vtmkzoom',
    }
    _TESTS = [{
        # vod
        'url': 'http://vtm.be/video/volledige-afleveringen/id/vtm_20170219_VM0678361_vtmwatch',
        'info_dict': {
            'id': 'vtm_20170219_VM0678361_vtmwatch',
            'ext': 'mp4',
            'title': 'Allemaal Chris afl. 6',
            'description': 'md5:4be86427521e7b07e0adb0c9c554ddb2',
            'timestamp': 1487533280,
            'upload_date': '20170219',
            'duration': 2562,
            'series': 'Allemaal Chris',
            'season': 'Allemaal Chris',
            'season_number': 1,
            'season_id': '256936078124527',
            'episode': 'Allemaal Chris afl. 6',
            'episode_number': 6,
            'episode_id': '256936078591527',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Requires account credentials',
    }, {
        # clip
        'url': 'http://vtm.be/video?aid=168332',
        'info_dict': {
            'id': '168332',
            'ext': 'mp4',
            'title': '"Veronique liegt!"',
            'description': 'md5:1385e2b743923afe54ba4adc38476155',
            'timestamp': 1489002029,
            'upload_date': '20170308',
            'duration': 96,
        },
    }, {
        # vod
        'url': 'http://vtm.be/video/volledige-afleveringen/id/257107153551000',
        'only_matching': True,
    }, {
        # vod
        'url': 'http://vtm.be/video?aid=163157',
        'only_matching': True,
    }, {
        # vod
        'url': 'http://www.q2.be/video/volledige-afleveringen/id/2be_20170301_VM0684442_q2',
        'only_matching': True,
    }, {
        # clip
        'url': 'http://vtmkzoom.be/k3-dansstudio/een-nieuw-seizoen-van-k3-dansstudio',
        'only_matching': True,
    }, {
        # http/s redirect
        'url': 'https://vtmkzoom.be/video?aid=45724',
        'info_dict': {
            'id': '257136373657000',
            'ext': 'mp4',
            'title': 'K3 Dansstudio Ushuaia afl.6',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Requires account credentials',
    }, {
        # nieuws.vtm.be
        'url': 'https://nieuws.vtm.be/stadion/stadion/genk-nog-moeilijk-programma',
        'only_matching': True,
    }]

    def _real_initialize(self):
        self._logged_in = False

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            self.raise_login_required()

        auth_data = {
            'APIKey': self._APIKEY,
            'sdk': 'js_6.1',
            'format': 'json',
            'loginID': username,
            'password': password,
        }

        auth_info = self._download_json(
            'https://accounts.eu1.gigya.com/accounts.login', None,
            note='Logging in', errnote='Unable to log in',
            data=urlencode_postdata(auth_data))

        error_message = auth_info.get('errorDetails') or auth_info.get('errorMessage')
        if error_message:
            raise ExtractorError(
                'Unable to login: %s' % error_message, expected=True)

        self._uid = auth_info['UID']
        self._uid_signature = auth_info['UIDSignature']
        self._signature_timestamp = auth_info['signatureTimestamp']

        self._logged_in = True

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id, site_id = mobj.group('id', 'site_id')

        webpage = self._download_webpage(url, video_id)

        config = self._parse_json(
            self._search_regex(
                r'videoJSConfig\s*=\s*JSON\.parse\(\'({.+?})\'\);',
                webpage, 'config', default='{}'), video_id,
            transform_source=lambda s: s.replace(
                '\\\\', '\\').replace(r'\"', '"').replace(r"\'", "'"))

        vod_id = config.get('vodId') or self._search_regex(
            (r'\\"vodId\\"\s*:\s*\\"(.+?)\\"',
             r'<[^>]+id=["\']vod-(\d+)'),
            webpage, 'video_id', default=None)

        # clip, no authentication required
        if not vod_id:
            player = self._parse_json(
                self._search_regex(
                    r'vmmaplayer\(({.+?})\);', webpage, 'vmma player',
                    default=''),
                video_id, transform_source=lambda s: '[%s]' % s, fatal=False)
            if player:
                video = player[-1]
                if video['videoUrl'] in ('http', 'https'):
                    return self.url_result(video['url'], MedialaanIE.ie_key())
                info = {
                    'id': video_id,
                    'url': video['videoUrl'],
                    'title': video['title'],
                    'thumbnail': video.get('imageUrl'),
                    'timestamp': int_or_none(video.get('createdDate')),
                    'duration': int_or_none(video.get('duration')),
                }
            else:
                info = self._parse_html5_media_entries(
                    url, webpage, video_id, m3u8_id='hls')[0]
                info.update({
                    'id': video_id,
                    'title': self._html_search_meta('description', webpage),
                    'duration': parse_duration(self._html_search_meta('duration', webpage)),
                })
        # vod, authentication required
        else:
            if not self._logged_in:
                self._login()

            settings = self._parse_json(
                self._search_regex(
                    r'jQuery\.extend\(Drupal\.settings\s*,\s*({.+?})\);',
                    webpage, 'drupal settings', default='{}'),
                video_id)

            def get(container, item):
                return try_get(
                    settings, lambda x: x[container][item],
                    compat_str) or self._search_regex(
                    r'"%s"\s*:\s*"([^"]+)' % item, webpage, item,
                    default=None)

            app_id = get('vod', 'app_id') or self._SITE_TO_APP_ID.get(site_id, 'vtm_watch')
            sso = get('vod', 'gigyaDatabase') or 'vtm-sso'

            data = self._download_json(
                'http://vod.medialaan.io/api/1.0/item/%s/video' % vod_id,
                video_id, query={
                    'app_id': app_id,
                    'user_network': sso,
                    'UID': self._uid,
                    'UIDSignature': self._uid_signature,
                    'signatureTimestamp': self._signature_timestamp,
                })

            formats = self._extract_m3u8_formats(
                data['response']['uri'], video_id, entry_protocol='m3u8_native',
                ext='mp4', m3u8_id='hls')

            self._sort_formats(formats)

            info = {
                'id': vod_id,
                'formats': formats,
            }

            api_key = get('vod', 'apiKey')
            channel = get('medialaanGigya', 'channel')

            if api_key:
                videos = self._download_json(
                    'http://vod.medialaan.io/vod/v2/videos', video_id, fatal=False,
                    query={
                        'channels': channel,
                        'ids': vod_id,
                        'limit': 1,
                        'apikey': api_key,
                    })
                if videos:
                    video = try_get(
                        videos, lambda x: x['response']['videos'][0], dict)
                    if video:
                        def get(container, item, expected_type=None):
                            return try_get(
                                video, lambda x: x[container][item], expected_type)

                        def get_string(container, item):
                            return get(container, item, compat_str)

                        info.update({
                            'series': get_string('program', 'title'),
                            'season': get_string('season', 'title'),
                            'season_number': int_or_none(get('season', 'number')),
                            'season_id': get_string('season', 'id'),
                            'episode': get_string('episode', 'title'),
                            'episode_number': int_or_none(get('episode', 'number')),
                            'episode_id': get_string('episode', 'id'),
                            'duration': int_or_none(
                                video.get('duration')) or int_or_none(
                                video.get('durationMillis'), scale=1000),
                            'title': get_string('episode', 'title'),
                            'description': get_string('episode', 'text'),
                            'timestamp': unified_timestamp(get_string(
                                'publication', 'begin')),
                        })

            if not info.get('title'):
                info['title'] = try_get(
                    config, lambda x: x['videoConfig']['title'],
                    compat_str) or self._html_search_regex(
                    r'\\"title\\"\s*:\s*\\"(.+?)\\"', webpage, 'title',
                    default=None) or self._og_search_title(webpage)

        if not info.get('description'):
            info['description'] = self._html_search_regex(
                r'<div[^>]+class="field-item\s+even">\s*<p>(.+?)</p>',
                webpage, 'description', default=None)

        return info
