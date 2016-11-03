# coding: utf-8
from __future__ import unicode_literals

import re
import time
import hashlib
import json

from .adobepass import AdobePassIE
from .common import InfoExtractor
from ..compat import compat_HTTPError
from ..utils import (
    int_or_none,
    parse_age_limit,
    str_or_none,
    parse_duration,
    ExtractorError,
    extract_attributes,
)


class ViceBaseIE(AdobePassIE):
    def _extract_preplay_video(self, url, webpage):
        watch_hub_data = extract_attributes(self._search_regex(
            r'(?s)(<watch-hub\s*.+?</watch-hub>)', webpage, 'watch hub'))
        video_id = watch_hub_data['vms-id']
        title = watch_hub_data['video-title']

        query = {}
        is_locked = watch_hub_data.get('video-locked') == '1'
        if is_locked:
            resource = self._get_mvpd_resource(
                'VICELAND', title, video_id,
                watch_hub_data.get('video-rating'))
            query['tvetoken'] = self._extract_mvpd_auth(url, video_id, 'VICELAND', resource)

        # signature generation algorithm is reverse engineered from signatureGenerator in
        # webpack:///../shared/~/vice-player/dist/js/vice-player.js in
        # https://www.viceland.com/assets/common/js/web.vendor.bundle.js
        exp = int(time.time()) + 14400
        query.update({
            'exp': exp,
            'sign': hashlib.sha512(('%s:GET:%d' % (video_id, exp)).encode()).hexdigest(),
        })

        try:
            host = 'www.viceland' if is_locked else self._PREPLAY_HOST
            preplay = self._download_json('https://%s.com/en_us/preplay/%s' % (host, video_id), video_id, query=query)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 400:
                error = json.loads(e.cause.read().decode())
                raise ExtractorError('%s said: %s' % (self.IE_NAME, error['details']), expected=True)
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
            'description': base.get('body'),
            'thumbnail': watch_hub_data.get('cover-image') or watch_hub_data.get('thumbnail'),
            'duration': parse_duration(video_data.get('video_duration') or watch_hub_data.get('video-duration')),
            'timestamp': int_or_none(video_data.get('created_at')),
            'age_limit': parse_age_limit(video_data.get('video_rating')),
            'series': video_data.get('show_title') or watch_hub_data.get('show-title'),
            'episode_number': int_or_none(episode.get('episode_number') or watch_hub_data.get('episode')),
            'episode_id': str_or_none(episode.get('id') or video_data.get('episode_id')),
            'season_number': int_or_none(watch_hub_data.get('season')),
            'season_id': str_or_none(episode.get('season_id')),
            'uploader': channel.get('base', {}).get('title') or watch_hub_data.get('channel-title'),
            'uploader_id': str_or_none(channel.get('id')),
            'subtitles': subtitles,
            'ie_key': 'UplynkPreplay',
        }


class ViceIE(ViceBaseIE):
    _VALID_URL = r'https?://(?:.+?\.)?vice\.com/(?:[^/]+/)?videos?/(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'http://www.vice.com/video/cowboy-capitalists-part-1',
        'md5': 'e9d77741f9e42ba583e683cd170660f7',
        'info_dict': {
            'id': '43cW1mYzpia9IlestBjVpd23Yu3afAfp',
            'ext': 'flv',
            'title': 'VICE_COWBOYCAPITALISTS_PART01_v1_VICE_WM_1080p.mov',
            'duration': 725.983,
        },
        'add_ie': ['Ooyala'],
    }, {
        'url': 'http://www.vice.com/video/how-to-hack-a-car',
        'md5': 'a7ecf64ee4fa19b916c16f4b56184ae2',
        'info_dict': {
            'id': '3jstaBeXgAs',
            'ext': 'mp4',
            'title': 'How to Hack a Car: Phreaked Out (Episode 2)',
            'description': 'md5:ee95453f7ff495db8efe14ae8bf56f30',
            'uploader_id': 'MotherboardTV',
            'uploader': 'Motherboard',
            'upload_date': '20140529',
        },
        'add_ie': ['Youtube'],
    }, {
        'url': 'https://video.vice.com/en_us/video/the-signal-from-tolva/5816510690b70e6c5fd39a56',
        'md5': '',
        'info_dict': {
            'id': '5816510690b70e6c5fd39a56',
            'ext': 'mp4',
            'uploader': 'Waypoint',
            'title': 'The Signal From Tölva',
            'uploader_id': '57f7d621e05ca860fa9ccaf9',
            'timestamp': 1477941983938,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'add_ie': ['UplynkPreplay'],
    }, {
        'url': 'https://news.vice.com/video/experimenting-on-animals-inside-the-monkey-lab',
        'only_matching': True,
    }, {
        'url': 'http://www.vice.com/ru/video/big-night-out-ibiza-clive-martin-229',
        'only_matching': True,
    }, {
        'url': 'https://munchies.vice.com/en/videos/watch-the-trailer-for-our-new-series-the-pizza-show',
        'only_matching': True,
    }]
    _PREPLAY_HOST = 'video.vice'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, urlh = self._download_webpage_handle(url, video_id)
        embed_code = self._search_regex(
            r'embedCode=([^&\'"]+)', webpage,
            'ooyala embed code', default=None)
        if embed_code:
            return self.url_result('ooyala:%s' % embed_code, 'Ooyala')
        youtube_id = self._search_regex(
            r'data-youtube-id="([^"]+)"', webpage, 'youtube id', default=None)
        if youtube_id:
            return self.url_result(youtube_id, 'Youtube')
        return self._extract_preplay_video(urlh.geturl(), webpage)


class ViceShowIE(InfoExtractor):
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
        description = self._html_search_meta('description', webpage, 'description')

        return self.playlist_result(entries, show_id, title, description)
