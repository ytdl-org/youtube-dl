# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    try_get,
    compat_str,
    unified_strdate,
    unified_timestamp,
    determine_ext,
    ExtractorError,
    clean_html,
)


class PivotshareBaseIE(InfoExtractor):
    _VALID_URL_BASE = r"""(?x)
        https?://
            (?:www\.)?
            (?P<domain>
                (?:
                    thunderboltpoweryogatv|
                    hungrymonkyoga|
                    soccer\.sklz|
                    womenstennisnetwork|
                    pigskinkids|
                    czwstudios|
                    highspotswrestlingnetwork|
                    titlematchwrestlingnetwork|
                    womenswrestlingnetwork|
                    rockstarpronetwork|
                    mcwragetv|
                    aawondemand|
                    pwnnetwork|
                    ondemand\.DiscoveryWrestling|
                    adsrcourses|
                    reaktortutorials|
                    crosscounter|
                    cultorama|
                    bongflix|
                    everyonecansalsa|
                    academy\.tedgibson|
                    video\.jasyoga|
                    (?P<subdomain>[^.]+)\.pivotshare
                )
                \.(?:com|tv)
            )?"""
    _API_BASE = 'https://api.pivotshare.com/v1/'
    _CLIENT_ID = 'c0da629bb49ceff00327ac7c1f128bca'
    _TOKEN = None
    _NETRC_MACHINE = 'pivotshare'


class PivotshareIE(PivotshareBaseIE):
    _VALID_URL = r"%s/media/(?:[^/]+)/(?P<id>[0-9]+)" % PivotshareBaseIE._VALID_URL_BASE
    _TESTS = [{
        'url': 'https://ted.pivotshare.com/media/rob-forbes-on-ways-of-seeing/61/feature',
        'md5': '30a2ba2b97d0a1ccd2efb5d534d922ae',
        'info_dict': {
            'id': '61',
            'ext': 'mp4',
            'title': 'Rob Forbes on ways of seeing',
            'description': 'md5:2dd273ce5f3e6fbb4c05d4be71db0174',
            'thumbnail': r're:^https?://.*\.(?:png|jpg)$',
            'uploader': 'Rob Forbes',
            'uploader_id': '28',
            'release_date': '20100909',
            'timestamp': 1284054573,
            'upload_date': '20100909',
            'channel': 'TED',
            'channel_id': 3,
            'channel_url': 'https://ted.pivotshare.com',
            'duration': 934,
            'categories': ['Arts']
        }
    }, {
        'url': 'https://www.hungrymonkyoga.com/media/home/9057/feature',
        'md5': '6a931de856aaa1c0956314a510e07e78',
        'info_dict': {
            'id': '9057',
            'ext': 'mp4',
            'title': 'Home',
            'description': 'md5:c2af199b6f178943676b78262b22c654',
            'thumbnail': r're:^https?://.*\.(?:png|jpg)$',
            'uploader': 'Bo Wang',
            'uploader_id': '2750',
            'release_date': '20140514',
            'timestamp': 1400056615,
            'upload_date': '20140514',
            'channel': 'Hungrymonk%20Yoga%E2%84%A2',
            'channel_id': 1769,
            'channel_url': 'www.hungrymonkyoga.com',
            'duration': 179,
            'categories': ['Hungrymonk Yoga']
        }
    }, {
        'url': 'https://www.highspotswrestlingnetwork.com/media/pwg%3A-mystery-vortex-6/97499/feature',
        'only_matching': True,
    }, {
        'url': 'https://video.jasyoga.com/media/functional-core/89966/?collectionId=3353',
        'only_matching': True,
    }]

    def _real_initialize(self):
        self._login()

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        login = self._download_json(
            '%slogin' % self._API_BASE, None, 'Logging in',
            data=json.dumps({
                'username': username,
                'password': password
            }).encode(),
            headers={
                'Content-Type': 'application/json'
            },
            query={
                'client_id': self._CLIENT_ID
            }, expected_status=401)

        if login.get('errors'):
            raise ExtractorError('Unable to login: %s' % clean_html(login['errors'][0]['message']), expected=True)
        else:
            self._TOKEN = try_get(login, lambda x: x['login']['access_token'], compat_str)

    def _real_extract(self, url):
        domain, subdomain, video_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, video_id)

        query = {
            'client_id': self._CLIENT_ID,
            'search_method': 'subdomain' if subdomain else 'domain'
        }
        if self._TOKEN:
            query['access_token'] = self._TOKEN

        channel_meta = self._download_json(
            '%schannels/%s' % (self._API_BASE, subdomain or domain),
            subdomain or domain, "Downloading channel JSON metadata",
            query=query)

        query.pop('search_method')

        channel_id = try_get(channel_meta, lambda x: x['channel']['id'], int)
        channel = try_get(channel_meta, lambda x: x['channel']['name'], compat_str)
        channel_url = try_get(channel_meta, lambda x: x['channel']['domain'], compat_str)
        if not channel_url:
            channel_url = 'https://%s.pivotshare.com' % try_get(
                channel_meta, lambda x: x['channel']['subdomain'], compat_str)

        meta = self._download_json(
            '%schannels/%s/media/%s' % (self._API_BASE, channel_id, video_id),
            video_id, "Downloading media JSON metadata",
            query=query)

        stream_data = self._download_json(
            '%schannels/%s/media/%s/stream' % (self._API_BASE, channel_id, video_id),
            video_id, "Downloading stream JSON metadata",
            query=query, expected_status=401)

        if stream_data.get('errors'):
            self.raise_login_required(
                'This video is only available for %s subscribers' % compat_urllib_parse_unquote(channel))

        sources = try_get(
            stream_data, lambda x: x['channel']['media']['stream']['formats'], list)
        formats = []
        if sources:
            for source in sources:
                if determine_ext(source.get('url')) == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        source.get('url'), video_id, 'mp4',
                        entry_protocol='m3u8_native', m3u8_id='hls',
                        fatal=False))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': try_get(meta, lambda x: x['channel']['media']['title'], compat_str) or self._og_search_title(webpage),
            'description': try_get(meta, lambda x: x['channel']['media']['description'], compat_str) or self._og_search_description(webpage),
            'thumbnail': try_get(meta, lambda x: x['channel']['media']['thumbnail_url']['large'], compat_str),
            'uploader': try_get(meta, lambda x: x['channel']['media']['author'], compat_str),
            'uploader_id': try_get(meta, lambda x: x['channel']['media']['author_id'], compat_str),
            'release_date': unified_strdate(try_get(meta, lambda x: x['channel']['media']['submit_date'], compat_str)),
            'timestamp': unified_timestamp(try_get(meta, lambda x: x['channel']['media']['submit_date'], compat_str)),
            'channel': channel,
            'channel_id': channel_id,
            'channel_url': channel_url,
            'duration': try_get(meta, lambda x: x['channel']['media']['duration'], int),
            'categories': [try_get(meta, lambda x: x['channel']['media']['category'], compat_str)],
        }


class PivotsharePlaylistIE(PivotshareBaseIE):
    _VALID_URL = r'%s/categories/(?:[^/]+)/(?P<id>[0-9]+)' % PivotshareBaseIE._VALID_URL_BASE
    _TESTS = [{
        'url': 'https://ted.pivotshare.com/categories/science/43/media',
        'info_dict': {
            'id': '43',
            'title': 'Science',
        },
    }]

    def _real_extract(self, url):
        domain, subdomain, playlist_id = re.match(self._VALID_URL, url).groups()

        query = {
            'client_id': self._CLIENT_ID,
            'search_method': 'subdomain' if subdomain else 'domain'
        }

        channel_meta = self._download_json(
            '%schannels/%s' % (self._API_BASE, subdomain or domain),
            subdomain or domain, "Downloading channel JSON metadata",
            query=query)

        query.pop('search_method')

        channel_id = try_get(channel_meta, lambda x: x['channel']['id'], int)

        if channel_id:
            category_meta = self._download_json(
                '%schannels/%s/categories/%s' % (
                    self._API_BASE, channel_id, playlist_id),
                playlist_id, "Downloading playlist JSON metadata",
                query=query)

            title = try_get(category_meta, lambda x: x['channel']['category']['name'], compat_str)

            category_items_meta = self._download_json(
                '%schannels/%s/categories/%s/media' % (
                    self._API_BASE, channel_id, playlist_id),
                playlist_id, "Downloading playlist items JSON metadata",
                query=query)

            entries = []

            for item in category_items_meta['categories']['media']:
                entries.append(self.url_result(
                    'https://%s/media/item/%s' % (
                        '%s.pivotshare.com' % subdomain if subdomain else domain,
                        item.get('id')), ie=PivotshareIE.ie_key()))

            return self.playlist_result(entries, playlist_id, title)
