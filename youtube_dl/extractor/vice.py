# coding: utf-8
from __future__ import unicode_literals

import re
import time
import hashlib
import json
import random

from .adobepass import AdobePassIE
from .youtube import YoutubeIE
from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_str,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_age_limit,
    str_or_none,
    try_get,
)


class ViceIE(AdobePassIE):
    IE_NAME = 'vice'
    _VALID_URL = r'https?://(?:(?:video|vms)\.vice|(?:www\.)?viceland)\.com/(?P<locale>[^/]+)/(?:video/[^/]+|embed)/(?P<id>[\da-f]+)'
    _TESTS = [{
        'url': 'https://video.vice.com/en_us/video/pet-cremator/58c69e38a55424f1227dc3f7',
        'info_dict': {
            'id': '5e647f0125e145c9aef2069412c0cbde',
            'ext': 'mp4',
            'title': '10 Questions You Always Wanted To Ask: Pet Cremator',
            'description': 'md5:fe856caacf61fe0e74fab15ce2b07ca5',
            'uploader': 'vice',
            'uploader_id': '57a204088cb727dec794c67b',
            'timestamp': 1489664942,
            'upload_date': '20170316',
            'age_limit': 14,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'add_ie': ['UplynkPreplay'],
    }, {
        # geo restricted to US
        'url': 'https://video.vice.com/en_us/video/the-signal-from-tolva/5816510690b70e6c5fd39a56',
        'info_dict': {
            'id': '930c0ad1f47141cc955087eecaddb0e2',
            'ext': 'mp4',
            'uploader': 'waypoint',
            'title': 'The Signal From Tölva',
            'description': 'md5:3927e3c79f9e8094606a2b3c5b5e55d5',
            'uploader_id': '57f7d621e05ca860fa9ccaf9',
            'timestamp': 1477941983,
            'upload_date': '20161031',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'add_ie': ['UplynkPreplay'],
    }, {
        'url': 'https://video.vice.com/alps/video/ulfs-wien-beruchtigste-grafitti-crew-part-1/581b12b60a0e1f4c0fb6ea2f',
        'info_dict': {
            'id': '581b12b60a0e1f4c0fb6ea2f',
            'ext': 'mp4',
            'title': 'ULFs - Wien berüchtigste Grafitti Crew - Part 1',
            'description': '<p>Zwischen Hinterzimmer-Tattoos und U-Bahnschächten erzählen uns die Ulfs, wie es ist, "süchtig nach Sachbeschädigung" zu sein.</p>',
            'uploader': 'VICE',
            'uploader_id': '57a204088cb727dec794c67b',
            'timestamp': 1485368119,
            'upload_date': '20170125',
            'age_limit': 14,
        },
        'params': {
            # AES-encrypted m3u8
            'skip_download': True,
            'proxy': '127.0.0.1:8118',
        },
        'add_ie': ['UplynkPreplay'],
    }, {
        'url': 'https://video.vice.com/en_us/video/pizza-show-trailer/56d8c9a54d286ed92f7f30e4',
        'only_matching': True,
    }, {
        'url': 'https://video.vice.com/en_us/embed/57f41d3556a0a80f54726060',
        'only_matching': True,
    }, {
        'url': 'https://vms.vice.com/en_us/video/preplay/58c69e38a55424f1227dc3f7',
        'only_matching': True,
    }, {
        'url': 'https://www.viceland.com/en_us/video/thursday-march-1-2018/5a8f2d7ff1cdb332dd446ec1',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe\b[^>]+\bsrc=["\']((?:https?:)?//video\.vice\.com/[^/]+/embed/[\da-f]+)',
            webpage)

    @staticmethod
    def _extract_url(webpage):
        urls = ViceIE._extract_urls(webpage)
        return urls[0] if urls else None

    def _real_extract(self, url):
        locale, video_id = re.match(self._VALID_URL, url).groups()

        webpage = self._download_webpage(
            'https://video.vice.com/%s/embed/%s' % (locale, video_id),
            video_id)

        video = self._parse_json(
            self._search_regex(
                r'PREFETCH_DATA\s*=\s*({.+?})\s*;\s*\n', webpage,
                'app state'), video_id)['video']
        video_id = video.get('vms_id') or video.get('id') or video_id
        title = video['title']
        is_locked = video.get('locked')
        rating = video.get('rating')
        thumbnail = video.get('thumbnail_url')
        duration = int_or_none(video.get('duration'))
        series = try_get(
            video, lambda x: x['episode']['season']['show']['title'],
            compat_str)
        episode_number = try_get(
            video, lambda x: x['episode']['episode_number'])
        season_number = try_get(
            video, lambda x: x['episode']['season']['season_number'])
        uploader = None

        query = {}
        if is_locked:
            resource = self._get_mvpd_resource(
                'VICELAND', title, video_id, rating)
            query['tvetoken'] = self._extract_mvpd_auth(
                url, video_id, 'VICELAND', resource)

        # signature generation algorithm is reverse engineered from signatureGenerator in
        # webpack:///../shared/~/vice-player/dist/js/vice-player.js in
        # https://www.viceland.com/assets/common/js/web.vendor.bundle.js
        # new JS is located here https://vice-web-statics-cdn.vice.com/vice-player/player-embed.js
        exp = int(time.time()) + 1440

        query.update({
            'exp': exp,
            'sign': hashlib.sha512(('%s:GET:%d' % (video_id, exp)).encode()).hexdigest(),
            '_ad_blocked': None,
            '_ad_unit': '',
            '_debug': '',
            'platform': 'desktop',
            'rn': random.randint(10000, 100000),
            'fbprebidtoken': '',
        })

        try:
            preplay = self._download_json(
                'https://vms.vice.com/%s/video/preplay/%s' % (locale, video_id),
                video_id, query=query)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code in (400, 401):
                error = json.loads(e.cause.read().decode())
                error_message = error.get('error_description') or error['details']
                raise ExtractorError('%s said: %s' % (
                    self.IE_NAME, error_message), expected=True)
            raise

        video_data = preplay['video']
        base = video_data['base']
        uplynk_preplay_url = preplay['preplayURL']
        episode = video_data.get('episode', {})
        channel = video_data.get('channel', {})

        subtitles = {}
        cc_url = preplay.get('ccURL')
        if cc_url:
            subtitles['en'] = [{
                'url': cc_url,
            }]

        return {
            '_type': 'url_transparent',
            'url': uplynk_preplay_url,
            'id': video_id,
            'title': title,
            'description': base.get('body') or base.get('display_body'),
            'thumbnail': thumbnail,
            'duration': int_or_none(video_data.get('video_duration')) or duration,
            'timestamp': int_or_none(video_data.get('created_at'), 1000),
            'age_limit': parse_age_limit(video_data.get('video_rating')),
            'series': video_data.get('show_title') or series,
            'episode_number': int_or_none(episode.get('episode_number') or episode_number),
            'episode_id': str_or_none(episode.get('id') or video_data.get('episode_id')),
            'season_number': int_or_none(season_number),
            'season_id': str_or_none(episode.get('season_id')),
            'uploader': channel.get('base', {}).get('title') or channel.get('name') or uploader,
            'uploader_id': str_or_none(channel.get('id')),
            'subtitles': subtitles,
            'ie_key': 'UplynkPreplay',
        }


class ViceShowIE(InfoExtractor):
    IE_NAME = 'vice:show'
    _VALID_URL = r'https?://(?:.+?\.)?vice\.com/(?:[^/]+/)?show/(?P<id>[^/?#&]+)'

    _TEST = {
        'url': 'https://munchies.vice.com/en/show/fuck-thats-delicious-2',
        'info_dict': {
            'id': 'fuck-thats-delicious-2',
            'title': "Fuck, That's Delicious",
            'description': 'Follow the culinary adventures of rapper Action Bronson during his ongoing world tour.',
        },
        'playlist_count': 17,
    }

    def _real_extract(self, url):
        show_id = self._match_id(url)
        webpage = self._download_webpage(url, show_id)

        entries = [
            self.url_result(video_url, ViceIE.ie_key())
            for video_url, _ in re.findall(
                r'<h2[^>]+class="article-title"[^>]+data-id="\d+"[^>]*>\s*<a[^>]+href="(%s.*?)"'
                % ViceIE._VALID_URL, webpage)]

        title = self._search_regex(
            r'<title>(.+?)</title>', webpage, 'title', default=None)
        if title:
            title = re.sub(r'(.+)\s*\|\s*.+$', r'\1', title).strip()
        description = self._html_search_meta(
            'description', webpage, 'description')

        return self.playlist_result(entries, show_id, title, description)


class ViceArticleIE(InfoExtractor):
    IE_NAME = 'vice:article'
    _VALID_URL = r'https://www\.vice\.com/[^/]+/article/(?P<id>[^?#]+)'

    _TESTS = [{
        'url': 'https://www.vice.com/en_us/article/on-set-with-the-woman-making-mormon-porn-in-utah',
        'info_dict': {
            'id': '41eae2a47b174a1398357cec55f1f6fc',
            'ext': 'mp4',
            'title': 'Mormon War on Porn ',
            'description': 'md5:6394a8398506581d0346b9ab89093fef',
            'uploader': 'vice',
            'uploader_id': '57a204088cb727dec794c67b',
            'timestamp': 1491883129,
            'upload_date': '20170411',
            'age_limit': 17,
        },
        'params': {
            # AES-encrypted m3u8
            'skip_download': True,
        },
        'add_ie': ['UplynkPreplay'],
    }, {
        'url': 'https://www.vice.com/en_us/article/how-to-hack-a-car',
        'md5': '7fe8ebc4fa3323efafc127b82bd821d9',
        'info_dict': {
            'id': '3jstaBeXgAs',
            'ext': 'mp4',
            'title': 'How to Hack a Car: Phreaked Out (Episode 2)',
            'description': 'md5:ee95453f7ff495db8efe14ae8bf56f30',
            'uploader': 'Motherboard',
            'uploader_id': 'MotherboardTV',
            'upload_date': '20140529',
        },
        'add_ie': ['Youtube'],
    }, {
        'url': 'https://www.vice.com/en_us/article/znm9dx/karley-sciortino-slutever-reloaded',
        'md5': 'a7ecf64ee4fa19b916c16f4b56184ae2',
        'info_dict': {
            'id': 'e2ed435eb67e43efb66e6ef9a6930a88',
            'ext': 'mp4',
            'title': "Making The World's First Male Sex Doll",
            'description': 'md5:916078ef0e032d76343116208b6cc2c4',
            'uploader': 'vice',
            'uploader_id': '57a204088cb727dec794c67b',
            'timestamp': 1476919911,
            'upload_date': '20161019',
            'age_limit': 17,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': [ViceIE.ie_key()],
    }, {
        'url': 'https://www.vice.com/en_us/article/cowboy-capitalists-part-1',
        'only_matching': True,
    }, {
        'url': 'https://www.vice.com/ru/article/big-night-out-ibiza-clive-martin-229',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        prefetch_data = self._parse_json(self._search_regex(
            r'__APP_STATE\s*=\s*({.+?})(?:\s*\|\|\s*{}\s*)?;\s*\n',
            webpage, 'app state'), display_id)['pageData']
        body = prefetch_data['body']

        def _url_res(video_url, ie_key):
            return {
                '_type': 'url_transparent',
                'url': video_url,
                'display_id': display_id,
                'ie_key': ie_key,
            }

        vice_url = ViceIE._extract_url(webpage)
        if vice_url:
            return _url_res(vice_url, ViceIE.ie_key())

        embed_code = self._search_regex(
            r'embedCode=([^&\'"]+)', body,
            'ooyala embed code', default=None)
        if embed_code:
            return _url_res('ooyala:%s' % embed_code, 'Ooyala')

        youtube_url = YoutubeIE._extract_url(body)
        if youtube_url:
            return _url_res(youtube_url, YoutubeIE.ie_key())

        video_url = self._html_search_regex(
            r'data-video-url="([^"]+)"',
            prefetch_data['embed_code'], 'video URL')

        return _url_res(video_url, ViceIE.ie_key())
