# coding: utf-8
from __future__ import unicode_literals

import base64
import json
import hashlib
import hmac
import random
import string
import time

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlencode,
    compat_urlparse,
)
from ..utils import (
    float_or_none,
    int_or_none,
)


class VRVBaseIE(InfoExtractor):
    _API_DOMAIN = None
    _API_PARAMS = {}
    _CMS_SIGNING = {}

    def _call_api(self, path, video_id, note, data=None):
        base_url = self._API_DOMAIN + '/core/' + path
        encoded_query = compat_urllib_parse_urlencode({
            'oauth_consumer_key': self._API_PARAMS['oAuthKey'],
            'oauth_nonce': ''.join([random.choice(string.ascii_letters) for _ in range(32)]),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': int(time.time()),
            'oauth_version': '1.0',
        })
        headers = self.geo_verification_headers()
        if data:
            data = json.dumps(data).encode()
            headers['Content-Type'] = 'application/json'
        method = 'POST' if data else 'GET'
        base_string = '&'.join([method, compat_urlparse.quote(base_url, ''), compat_urlparse.quote(encoded_query, '')])
        oauth_signature = base64.b64encode(hmac.new(
            (self._API_PARAMS['oAuthSecret'] + '&').encode('ascii'),
            base_string.encode(), hashlib.sha1).digest()).decode()
        encoded_query += '&oauth_signature=' + compat_urlparse.quote(oauth_signature, '')
        return self._download_json(
            '?'.join([base_url, encoded_query]), video_id,
            note='Downloading %s JSON metadata' % note, headers=headers, data=data)

    def _call_cms(self, path, video_id, note):
        if not self._CMS_SIGNING:
            self._CMS_SIGNING = self._call_api('index', video_id, 'CMS Signing')['cms_signing']
        return self._download_json(
            self._API_DOMAIN + path, video_id, query=self._CMS_SIGNING,
            note='Downloading %s JSON metadata' % note, headers=self.geo_verification_headers())

    def _set_api_params(self, webpage, video_id):
        if not self._API_PARAMS:
            self._API_PARAMS = self._parse_json(self._search_regex(
                r'window\.__APP_CONFIG__\s*=\s*({.+?})</script>',
                webpage, 'api config'), video_id)['cxApiParams']
            self._API_DOMAIN = self._API_PARAMS.get('apiDomain', 'https://api.vrv.co')

    def _get_cms_resource(self, resource_key, video_id):
        return self._call_api(
            'cms_resource', video_id, 'resource path', data={
                'resource_key': resource_key,
            })['__links__']['cms_resource']['href']


class VRVIE(VRVBaseIE):
    IE_NAME = 'vrv'
    _VALID_URL = r'https?://(?:www\.)?vrv\.co/watch/(?P<id>[A-Z0-9]+)'
    _TEST = {
        'url': 'https://vrv.co/watch/GR9PNZ396/Hidden-America-with-Jonah-Ray:BOSTON-WHERE-THE-PAST-IS-THE-PRESENT',
        'info_dict': {
            'id': 'GR9PNZ396',
            'ext': 'mp4',
            'title': 'BOSTON: WHERE THE PAST IS THE PRESENT',
            'description': 'md5:4ec8844ac262ca2df9e67c0983c6b83f',
            'uploader_id': 'seeso',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            url, video_id,
            headers=self.geo_verification_headers())
        media_resource = self._parse_json(self._search_regex(
            r'window\.__INITIAL_STATE__\s*=\s*({.+?})</script>',
            webpage, 'inital state'), video_id).get('watch', {}).get('mediaResource') or {}

        video_data = media_resource.get('json')
        if not video_data:
            self._set_api_params(webpage, video_id)
            episode_path = self._get_cms_resource(
                'cms:/episodes/' + video_id, video_id)
            video_data = self._call_cms(episode_path, video_id, 'video')
        title = video_data['title']

        streams_json = media_resource.get('streams', {}).get('json', {})
        if not streams_json:
            self._set_api_params(webpage, video_id)
            streams_path = video_data['__links__']['streams']['href']
            streams_json = self._call_cms(streams_path, video_id, 'streams')

        audio_locale = streams_json.get('audio_locale')
        formats = []
        for stream_type, streams in streams_json.get('streams', {}).items():
            if stream_type in ('adaptive_hls', 'adaptive_dash'):
                for stream in streams.values():
                    stream_url = stream.get('url')
                    if not stream_url:
                        continue
                    stream_id = stream.get('hardsub_locale') or audio_locale
                    format_id = '%s-%s' % (stream_type.split('_')[1], stream_id)
                    if stream_type == 'adaptive_hls':
                        adaptive_formats = self._extract_m3u8_formats(
                            stream_url, video_id, 'mp4', m3u8_id=format_id,
                            note='Downloading %s m3u8 information' % stream_id,
                            fatal=False)
                    else:
                        adaptive_formats = self._extract_mpd_formats(
                            stream_url, video_id, mpd_id=format_id,
                            note='Downloading %s MPD information' % stream_id,
                            fatal=False)
                    if audio_locale:
                        for f in adaptive_formats:
                            if f.get('acodec') != 'none':
                                f['language'] = audio_locale
                    formats.extend(adaptive_formats)
        self._sort_formats(formats)

        subtitles = {}
        for subtitle in streams_json.get('subtitles', {}).values():
            subtitle_url = subtitle.get('url')
            if not subtitle_url:
                continue
            subtitles.setdefault(subtitle.get('locale', 'en-US'), []).append({
                'url': subtitle_url,
                'ext': subtitle.get('format', 'ass'),
            })

        thumbnails = []
        for thumbnail in video_data.get('images', {}).get('thumbnails', []):
            thumbnail_url = thumbnail.get('source')
            if not thumbnail_url:
                continue
            thumbnails.append({
                'url': thumbnail_url,
                'width': int_or_none(thumbnail.get('width')),
                'height': int_or_none(thumbnail.get('height')),
            })

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': thumbnails,
            'description': video_data.get('description'),
            'duration': float_or_none(video_data.get('duration_ms'), 1000),
            'uploader_id': video_data.get('channel_id'),
            'series': video_data.get('series_title'),
            'season': video_data.get('season_title'),
            'season_number': int_or_none(video_data.get('season_number')),
            'season_id': video_data.get('season_id'),
            'episode': title,
            'episode_number': int_or_none(video_data.get('episode_number')),
            'episode_id': video_data.get('production_episode_id'),
        }


class VRVSeriesIE(VRVBaseIE):
    IE_NAME = 'vrv:series'
    _VALID_URL = r'https?://(?:www\.)?vrv\.co/series/(?P<id>[A-Z0-9]+)'
    _TEST = {
        'url': 'https://vrv.co/series/G68VXG3G6/The-Perfect-Insider',
        'info_dict': {
            'id': 'G68VXG3G6',
        },
        'playlist_mincount': 11,
    }

    def _real_extract(self, url):
        series_id = self._match_id(url)
        webpage = self._download_webpage(
            url, series_id,
            headers=self.geo_verification_headers())

        self._set_api_params(webpage, series_id)
        seasons_path = self._get_cms_resource(
            'cms:/seasons?series_id=' + series_id, series_id)
        seasons_data = self._call_cms(seasons_path, series_id, 'seasons')

        entries = []
        for season in seasons_data.get('items', []):
            episodes_path = season['__links__']['season/episodes']['href']
            episodes = self._call_cms(episodes_path, series_id, 'episodes')
            for episode in episodes.get('items', []):
                episode_id = episode['id']
                entries.append(self.url_result(
                    'https://vrv.co/watch/' + episode_id,
                    'VRV', episode_id, episode.get('title')))

        return self.playlist_result(entries, series_id)
