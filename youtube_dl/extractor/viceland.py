# coding: utf-8
from __future__ import unicode_literals

import time
import hashlib
import json

from .adobepass import AdobePassIE
from ..compat import compat_HTTPError
from ..utils import (
    int_or_none,
    parse_age_limit,
    str_or_none,
    parse_duration,
    ExtractorError,
    extract_attributes,
)


class VicelandIE(AdobePassIE):
    _VALID_URL = r'https?://(?:www\.)?viceland\.com/[^/]+/video/[^/]+/(?P<id>[a-f0-9]+)'
    _TEST = {
        'url': 'https://www.viceland.com/en_us/video/cyberwar-trailer/57608447973ee7705f6fbd4e',
        'info_dict': {
            'id': '57608447973ee7705f6fbd4e',
            'ext': 'mp4',
            'title': 'CYBERWAR (Trailer)',
            'description': 'Tapping into the geopolitics of hacking and surveillance, Ben Makuch travels the world to meet with hackers, government officials, and dissidents to investigate the ecosystem of cyberwarfare.',
            'age_limit': 14,
            'timestamp': 1466008539,
            'upload_date': '20160615',
            'uploader_id': '11',
            'uploader': 'Viceland',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'add_ie': ['UplynkPreplay'],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        watch_hub_data = extract_attributes(self._search_regex(
            r'(?s)(<watch-hub\s*.+?</watch-hub>)', webpage, 'watch hub'))
        video_id = watch_hub_data['vms-id']
        title = watch_hub_data['video-title']

        query = {}
        if watch_hub_data.get('video-locked') == '1':
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
            preplay = self._download_json('https://www.viceland.com/en_us/preplay/%s' % video_id, video_id, query=query)
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
