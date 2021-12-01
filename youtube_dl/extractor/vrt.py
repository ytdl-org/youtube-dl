# coding: utf-8
from __future__ import unicode_literals

import re
import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    float_or_none,
    get_element_by_class,
    parse_iso8601,
    str_or_none,
    strip_or_none,
    unified_strdate,
    unified_timestamp,
    url_or_none,
)


class VRTIE(InfoExtractor):
    _TOKEN_URL = 'https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/tokens'

    _HLS_ENTRY_PROTOCOLS_MAP = {
        'HLS': 'm3u8_native',
        'HLS_AES': 'm3u8',
    }

    IE_DESC = 'VRT NWS, Flanders News, Flandern Info and Sporza'
    _VALID_URL = r'https?://(?:www\.)?(?P<site>vrt\.be/vrtnws|sporza\.be)/[a-z]{2}/\d{4}/\d{2}/\d{2}/(?P<id>[^/?&#]+)'
    _TESTS = [
        {
            'url': 'https://www.vrt.be/vrtnws/nl/2021/03/17/phishing-is-booming/',
            'md5': '989a49115048a820a96ff7abefb47726',
            'info_dict': {
                'id': 'pbs-pub-a2ceca71-a412-4b56-9d75-04bd6c29d50a$vid-8da4850b-372a-4cc1-92ab-c06b28c4b1f7',
                'ext': 'mp4',
                'title': 'KLAAR: Phishing is booming',
                'timestamp': 1615982100,
                'upload_date': '20210317',
                'duration': 225.12,
            },
        }, {
            'url': 'https://www.vrt.be/vrtnws/nl/2019/05/15/beelden-van-binnenkant-notre-dame-een-maand-na-de-brand/',
            'md5': 'e1663accf5cf13f375f3cd0d10476669',
            'info_dict': {
                'id': 'pbs-pub-7855fc7b-1448-49bc-b073-316cb60caa71$vid-2ca50305-c38a-4762-9890-65cbd098b7bd',
                'ext': 'mp4',
                'title': 'Beelden van binnenkant Notre-Dame, één maand na de brand',
                'description': 'Intussen is overigens gebleken dat een groot deel van het geld voor de herstelling nog altijd niet binnen is.',
                'timestamp': 1557924660,
                'upload_date': '20190515',
                'duration': 31.2,
            },
        }, {
            'url': 'https://sporza.be/nl/2019/05/15/de-belgian-cats-zijn-klaar-voor-het-ek/',
            'md5': '910bba927566e9ab992278f647eb4b75',
            'info_dict': {
                'id': 'pbs-pub-f2c86a46-8138-413a-a4b9-a0015a16ce2c$vid-1f112b31-e58e-4379-908d-aca6d80f8818',
                'ext': 'mp4',
                'title': 'De Belgian Cats zijn klaar voor het EK mét Ann Wauters',
                'timestamp': 1557923760,
                'upload_date': '20190515',
                'duration': 115.17,
            },
        }, {
            'url': 'https://www.vrt.be/vrtnws/en/2019/05/15/belgium_s-eurovision-entry-falls-at-the-first-hurdle/',
            'md5': 'e1d5cc5af9ac31e6a26c35cd456001a4',
            'info_dict': {
                'id': 'pbs-pub-857a6e18-44b5-4be1-91b6-6932a4c5363b$vid-704387c8-5bb5-430e-b1a8-cd5e2f7c3c6d',
                'ext': 'mp4',
                'title': "Belgium’s Eurovision entry falls at the first hurdle",
                'timestamp': 1557909120,
                'duration': 178.19,
                'upload_date': '20190515',
                'description': '18-year-old Eliot’s rendition of the song “Wake Up” was not among the 10 song’s to go through from Tuesday evening’s first semi-final.',
            },
        }
    ]
    _CLIENT_MAP = {
        'vrt.be/vrtnws': 'vrtnieuws',
        'sporza.be': 'sporza',
    }

    last_token_value = None
    last_token_expiration = None

    def _get_playertoken(self):
        if not self.last_token_expiration or self.last_token_expiration < time.time():
            headers = self.geo_verification_headers()
            headers.update({'Content-Type': 'application/json'})
            token_json = self._download_json(
                self._TOKEN_URL, None,
                'Downloading token', data=b'', headers=headers)

            self.last_token_value = token_json.get('vrtPlayerToken')
            self.last_token_expiration = parse_iso8601(token_json.get('expirationDate'))
        return self.last_token_value

    def _real_extract(self, url):
        site_id, display_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, display_id)
        attrs = extract_attributes(self._search_regex(
            r'(<[^>]+class="vrtvideo[^>]*>)', webpage, 'vrt video'))

        video_id = attrs.get('data-video-id') or attrs.get('data-videoid')
        publication_id = attrs.get('data-publication-id') or attrs.get('data-publicationid')
        if publication_id:
            video_id = publication_id + '$' + video_id
        api_url = attrs.get('data-media-api-url') or attrs.get('data-mediaapiurl')
        client_code = attrs.get('data-client-code') or attrs.get('data-client')

        title = strip_or_none(get_element_by_class(
            'vrt-title', webpage) or self._html_search_meta(
            ['og:title', 'twitter:title', 'name'], webpage))
        description = self._html_search_meta(
            ['og:description', 'twitter:description', 'description'], webpage, default=None, fatal=False)
        if description == '…':
            description = None
        timestamp = unified_timestamp(self._html_search_meta(
            'article:published_time', webpage))

        analytics = attrs['data-analytics']
        publication_date = unified_strdate(self._parse_json(analytics, video_id).get('publication_date'))

        # this might be reused from a previous run
        playertoken = self._get_playertoken()

        # get media_services video descriptor
        media_info = self._download_json(
            '{api_url}/videos/{video_id}'.format(api_url=api_url, video_id=video_id),
            video_id,
            note="Downloading video info",
            query={
                'vrtPlayerToken': playertoken,
                'client': client_code,
            })
        if not media_info.get('title'):
            code = media_info.get('code')
            if code == 'AUTHENTICATION_REQUIRED':
                self.raise_login_required()
            elif code == 'INVALID_LOCATION':
                self.raise_geo_restricted(countries=['BE'])
            else:
                raise ExtractorError(media_info.get('message') or code, expected=True)

        formats = []
        for target in media_info['targetUrls']:
            format_url, format_type = url_or_none(target.get('url')), str_or_none(target.get('type'))
            if not format_url or not format_type:
                continue
            format_type = format_type.upper()
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

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'display_id': display_id,
            'thumbnail': attrs.get('data-posterimage'),
            'duration': float_or_none(attrs.get('data-duration'), 1000),
            'timestamp': timestamp,
            'upload_date': publication_date,
            'formats': formats,
        }
