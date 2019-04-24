# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urllib_parse_urlparse
)
from ..utils import (
    extract_attributes,
    float_or_none,
    int_or_none,
    str_or_none,
)


class STVPlayerIE(InfoExtractor):
    IE_NAME = 'stv:player'
    _VALID_URL = r'https?://player\.stv\.tv/(?P<type>episode|video)/(?P<id>[a-z0-9]{4})'
    _TEST = {
        'url': 'https://player.stv.tv/video/7srz/victoria/interview-with-the-cast-ahead-of-new-victoria/',
        'md5': '2ad867d4afd641fa14187596e0fbc91b',
        'info_dict': {
            'id': '6016487034001',
            'ext': 'mp4',
            'upload_date': '20190321',
            'title': 'Interview with the cast ahead of new Victoria',
            'description': 'Nell Hudson and Lily Travers tell us what to expect in the new season of Victoria.',
            'timestamp': 1553179628,
            'uploader_id': '1486976045',
        },
        'skip': 'this resource is unavailable outside of the UK',
    }
    _PUBLISHER_ID = '1486976045'
    _PTYPE_MAP = {
        'episode': 'episodes',
        'video': 'shortform',
    }

    def _real_extract(self, url):
        ptype, video_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, video_id)

        qs = compat_parse_qs(compat_urllib_parse_urlparse(self._search_regex(
            r'itemprop="embedURL"[^>]+href="([^"]+)',
            webpage, 'embed URL', default=None)).query)
        publisher_id = qs.get('publisherID', [None])[0] or self._PUBLISHER_ID

        player_attr = extract_attributes(self._search_regex(
            r'(<[^>]+class="bcplayer"[^>]+>)', webpage, 'player', default=None)) or {}

        info = {}
        duration = ref_id = series = video_id = None
        api_ref_id = player_attr.get('data-player-api-refid')
        if api_ref_id:
            resp = self._download_json(
                'https://player.api.stv.tv/v1/%s/%s' % (self._PTYPE_MAP[ptype], api_ref_id),
                api_ref_id, fatal=False)
            if resp:
                result = resp.get('results') or {}
                video = result.get('video') or {}
                video_id = str_or_none(video.get('id'))
                ref_id = video.get('guid')
                duration = video.get('length')
                programme = result.get('programme') or {}
                series = programme.get('name') or programme.get('shortName')
                subtitles = {}
                _subtitles = result.get('_subtitles') or {}
                for ext, sub_url in _subtitles.items():
                    subtitles.setdefault('en', []).append({
                        'ext': 'vtt' if ext == 'webvtt' else ext,
                        'url': sub_url,
                    })
                info.update({
                    'description': result.get('summary'),
                    'subtitles': subtitles,
                    'view_count': int_or_none(result.get('views')),
                })
        if not video_id:
            video_id = qs.get('videoId', [None])[0] or self._search_regex(
                r'<link\s+itemprop="url"\s+href="(\d+)"',
                webpage, 'video id', default=None) or 'ref:' + (ref_id or player_attr['data-refid'])

        info.update({
            '_type': 'url_transparent',
            'duration': float_or_none(duration or player_attr.get('data-duration'), 1000),
            'id': video_id,
            'ie_key': 'BrightcoveNew',
            'series': series or player_attr.get('data-programme-name'),
            'url': 'http://players.brightcove.net/%s/default_default/index.html?videoId=%s' % (publisher_id, video_id),
        })
        return info
