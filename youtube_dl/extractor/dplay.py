# coding: utf-8
from __future__ import unicode_literals

import json
import re
import time

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
    compat_HTTPError,
)
from ..utils import (
    USER_AGENTS,
    ExtractorError,
    int_or_none,
    unified_strdate,
    remove_end,
    update_url_query,
)


class DPlayIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<domain>www\.dplay\.(?:dk|se|no))/[^/]+/(?P<id>[^/?#]+)'

    _TESTS = [{
        # non geo restricted, via secure api, unsigned download hls URL
        'url': 'http://www.dplay.se/nugammalt-77-handelser-som-format-sverige/season-1-svensken-lar-sig-njuta-av-livet/',
        'info_dict': {
            'id': '3172',
            'display_id': 'season-1-svensken-lar-sig-njuta-av-livet',
            'ext': 'mp4',
            'title': 'Svensken lär sig njuta av livet',
            'description': 'md5:d3819c9bccffd0fe458ca42451dd50d8',
            'duration': 2650,
            'timestamp': 1365454320,
            'upload_date': '20130408',
            'creator': 'Kanal 5 (Home)',
            'series': 'Nugammalt - 77 händelser som format Sverige',
            'season_number': 1,
            'episode_number': 1,
            'age_limit': 0,
        },
    }, {
        # geo restricted, via secure api, unsigned download hls URL
        'url': 'http://www.dplay.dk/mig-og-min-mor/season-6-episode-12/',
        'info_dict': {
            'id': '70816',
            'display_id': 'season-6-episode-12',
            'ext': 'mp4',
            'title': 'Episode 12',
            'description': 'md5:9c86e51a93f8a4401fc9641ef9894c90',
            'duration': 2563,
            'timestamp': 1429696800,
            'upload_date': '20150422',
            'creator': 'Kanal 4 (Home)',
            'series': 'Mig og min mor',
            'season_number': 6,
            'episode_number': 12,
            'age_limit': 0,
        },
    }, {
        # geo restricted, via direct unsigned hls URL
        'url': 'http://www.dplay.no/pga-tour/season-1-hoydepunkter-18-21-februar/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')
        domain = mobj.group('domain')

        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            r'data-video-id=["\'](\d+)', webpage, 'video id')

        info = self._download_json(
            'http://%s/api/v2/ajax/videos?video_id=%s' % (domain, video_id),
            video_id)['data'][0]

        title = info['title']

        PROTOCOLS = ('hls', 'hds')
        formats = []

        def extract_formats(protocol, manifest_url):
            if protocol == 'hls':
                m3u8_formats = self._extract_m3u8_formats(
                    manifest_url, video_id, ext='mp4',
                    entry_protocol='m3u8_native', m3u8_id=protocol, fatal=False)
                # Sometimes final URLs inside m3u8 are unsigned, let's fix this
                # ourselves. Also fragments' URLs are only served signed for
                # Safari user agent.
                query = compat_urlparse.parse_qs(compat_urlparse.urlparse(manifest_url).query)
                for m3u8_format in m3u8_formats:
                    m3u8_format.update({
                        'url': update_url_query(m3u8_format['url'], query),
                        'http_headers': {
                            'User-Agent': USER_AGENTS['Safari'],
                        },
                    })
                formats.extend(m3u8_formats)
            elif protocol == 'hds':
                formats.extend(self._extract_f4m_formats(
                    manifest_url + '&hdcore=3.8.0&plugin=flowplayer-3.8.0.0',
                    video_id, f4m_id=protocol, fatal=False))

        domain_tld = domain.split('.')[-1]
        if domain_tld in ('se', 'dk', 'no'):
            for protocol in PROTOCOLS:
                # Providing dsc-geo allows to bypass geo restriction in some cases
                self._set_cookie(
                    'secure.dplay.%s' % domain_tld, 'dsc-geo',
                    json.dumps({
                        'countryCode': domain_tld.upper(),
                        'expiry': (time.time() + 20 * 60) * 1000,
                    }))
                stream = self._download_json(
                    'https://secure.dplay.%s/secure/api/v2/user/authorization/stream/%s?stream_type=%s'
                    % (domain_tld, video_id, protocol), video_id,
                    'Downloading %s stream JSON' % protocol, fatal=False)
                if stream and stream.get(protocol):
                    extract_formats(protocol, stream[protocol])

        # The last resort is to try direct unsigned hls/hds URLs from info dictionary.
        # Sometimes this does work even when secure API with dsc-geo has failed (e.g.
        # http://www.dplay.no/pga-tour/season-1-hoydepunkter-18-21-februar/).
        if not formats:
            for protocol in PROTOCOLS:
                if info.get(protocol):
                    extract_formats(protocol, info[protocol])

        self._sort_formats(formats)

        subtitles = {}
        for lang in ('se', 'sv', 'da', 'nl', 'no'):
            for format_id in ('web_vtt', 'vtt', 'srt'):
                subtitle_url = info.get('subtitles_%s_%s' % (lang, format_id))
                if subtitle_url:
                    subtitles.setdefault(lang, []).append({'url': subtitle_url})

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': info.get('video_metadata_longDescription'),
            'duration': int_or_none(info.get('video_metadata_length'), scale=1000),
            'timestamp': int_or_none(info.get('video_publish_date')),
            'creator': info.get('video_metadata_homeChannel'),
            'series': info.get('video_metadata_show'),
            'season_number': int_or_none(info.get('season')),
            'episode_number': int_or_none(info.get('episode')),
            'age_limit': int_or_none(info.get('minimum_age')),
            'formats': formats,
            'subtitles': subtitles,
        }


class DPlayItIE(InfoExtractor):
    _VALID_URL = r'https?://it\.dplay\.com/[^/]+/[^/]+/(?P<id>[^/?#]+)'
    _GEO_COUNTRIES = ['IT']
    _TEST = {
        'url': 'http://it.dplay.com/nove/biografie-imbarazzanti/luigi-di-maio-la-psicosi-di-stanislawskij/',
        'md5': '2b808ffb00fc47b884a172ca5d13053c',
        'info_dict': {
            'id': '6918',
            'display_id': 'luigi-di-maio-la-psicosi-di-stanislawskij',
            'ext': 'mp4',
            'title': 'Biografie imbarazzanti: Luigi Di Maio: la psicosi di Stanislawskij',
            'description': 'md5:3c7a4303aef85868f867a26f5cc14813',
            'thumbnail': r're:^https?://.*\.jpe?g',
            'upload_date': '20160524',
            'series': 'Biografie imbarazzanti',
            'season_number': 1,
            'episode': 'Luigi Di Maio: la psicosi di Stanislawskij',
            'episode_number': 1,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        info_url = self._search_regex(
            r'url\s*:\s*["\']((?:https?:)?//[^/]+/playback/videoPlaybackInfo/\d+)',
            webpage, 'video id')

        title = remove_end(self._og_search_title(webpage), ' | Dplay')

        try:
            info = self._download_json(
                info_url, display_id, headers={
                    'Authorization': 'Bearer %s' % self._get_cookies(url).get(
                        'dplayit_token').value,
                    'Referer': url,
                })
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code in (400, 403):
                info = self._parse_json(e.cause.read().decode('utf-8'), display_id)
                error = info['errors'][0]
                if error.get('code') == 'access.denied.geoblocked':
                    self.raise_geo_restricted(
                        msg=error.get('detail'), countries=self._GEO_COUNTRIES)
                raise ExtractorError(info['errors'][0]['detail'], expected=True)
            raise

        hls_url = info['data']['attributes']['streaming']['hls']['url']

        formats = self._extract_m3u8_formats(
            hls_url, display_id, ext='mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')

        series = self._html_search_regex(
            r'(?s)<h1[^>]+class=["\'].*?\bshow_title\b.*?["\'][^>]*>(.+?)</h1>',
            webpage, 'series', fatal=False)
        episode = self._search_regex(
            r'<p[^>]+class=["\'].*?\bdesc_ep\b.*?["\'][^>]*>\s*<br/>\s*<b>([^<]+)',
            webpage, 'episode', fatal=False)

        mobj = re.search(
            r'(?s)<span[^>]+class=["\']dates["\'][^>]*>.+?\bS\.(?P<season_number>\d+)\s+E\.(?P<episode_number>\d+)\s*-\s*(?P<upload_date>\d{2}/\d{2}/\d{4})',
            webpage)
        if mobj:
            season_number = int(mobj.group('season_number'))
            episode_number = int(mobj.group('episode_number'))
            upload_date = unified_strdate(mobj.group('upload_date'))
        else:
            season_number = episode_number = upload_date = None

        return {
            'id': info_url.rpartition('/')[-1],
            'display_id': display_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'series': series,
            'season_number': season_number,
            'episode': episode,
            'episode_number': episode_number,
            'upload_date': upload_date,
            'formats': formats,
        }
