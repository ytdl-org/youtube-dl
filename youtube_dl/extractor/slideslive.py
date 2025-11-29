# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    bool_or_none,
    extract_attributes,
    int_or_none,
    smuggle_url,
    try_get,
    unified_timestamp,
    url_or_none,
)


class SlidesLiveIE(InfoExtractor):
    _VALID_URL = r'https?://slideslive\.com/(?P<id>[0-9]+)'
    _TESTS = [{
        # video_service_name = YOUTUBE
        'url': 'https://slideslive.com/38902413/gcc-ia16-backend',
        'md5': 'b29fcd6c6952d0c79c5079b0e7a07e6f',
        'info_dict': {
            'id': 'LMtgR8ba0b0',
            'ext': 'mp4',
            'title': 'GCC IA16 backend',
            'description': 'Watch full version of this video at https://slideslive.com/38902413.',
            'uploader': 'SlidesLive Videos - A',
            'uploader_id': 'UC62SdArr41t_-_fX40QCLRw',
            'timestamp': 1618809663,
            'upload_date': '20170925',
        }
    }, {
        # video_service_name = yoda
        'url': 'https://slideslive.com/38935785',
        'md5': '575cd7a6c0acc6e28422fe76dd4bcb1a',  # d735b130beb40013a839de1c58a74689
        'info_dict': {
            'id': 'F31OTzeGyDK_',
            'display_id': '38935785',
            'ext': 'mp4',
            'title': 'Offline Reinforcement Learning: From Algorithms to Practical Challenges',
            'upload_date': '20210220',
            'timestamp': 1613785940,
        },
        'params': {
            'format': 'bestvideo',
        },
    }, {
        # video_service_name = youtube
        'url': 'https://slideslive.com/38903721/magic-a-scientific-resurrection-of-an-esoteric-legend',
        'only_matching': True,
    }, {
        # video_service_name = url
        'url': 'https://slideslive.com/38922070/learning-transferable-skills-1',
        'only_matching': True,
    }, {
        # video_service_name = vimeo
        'url': 'https://slideslive.com/38921896/retrospectives-a-venue-for-selfreflection-in-ml-research-3',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        player = self._search_regex(
            r'<div\s[^>]*?id\s*=\s*(?P<q>\'|"|\b)player(?P=q)(?:\s[^>]*)?>.*?</div>',
            webpage, 'player div', fatal=False, group=0)
        player = (player and extract_attributes(player)) or {}
        token = player.get('data-player-token')
        if not token:
            raise ExtractorError('Unable to get player token', expected=True)
        video_data = self._download_json(
            'https://ben.slideslive.com/player/' + video_id, video_id,
            query={'player_token': token, })
        service_name = video_data['video_service_name'].lower()
        assert service_name in ('url', 'yoda', 'vimeo', 'youtube')
        service_id = video_data['video_service_id']
        subtitles = {}
        for sub in try_get(video_data, lambda x: x['subtitles'], list) or []:
            if not isinstance(sub, dict):
                continue
            webvtt_url = url_or_none(sub.get('webvtt_url'))
            if not webvtt_url:
                continue
            lang = sub.get('language') or 'en'
            subtitles.setdefault(lang, []).append({
                'url': webvtt_url,
            })
        info = {
            'id': video_id,
            'thumbnail': video_data.get(
                'thumbnail',
                self._html_search_meta(('thumbnailUrl', 'thumbnailURL'), webpage)),
            'is_live': bool_or_none(video_data.get('is_live')),
            'subtitles': subtitles,
            'timestamp': (
                int_or_none(video_data.get('updated_at'))
                or unified_timestamp(
                    self._html_search_meta('uploadDate', webpage))),
            'creator': self._og_search_property('author', webpage, fatal=False),
        }
        title = (
            video_data.get('title')
            or self._html_search_meta('name', webpage, display_name='meta title')
            or self._og_search_title(webpage, fatal=False))
        if service_name in ('url', 'yoda'):
            info['title'] = title or video_data['title']
            if service_name == 'url':
                info['url'] = service_id
            else:
                formats = []
                _MANIFEST_PATTERN = 'https://01.cdn.yoda.slideslive.com/%s/master.%s'
                # use `m3u8` entry_protocol until EXT-X-MAP is properly supported by `m3u8_native` entry_protocol
                formats.extend(self._extract_m3u8_formats(
                    _MANIFEST_PATTERN % (service_id, 'm3u8'),
                    service_id, 'mp4', m3u8_id='hls', fatal=False))
                formats.extend(self._extract_mpd_formats(
                    _MANIFEST_PATTERN % (service_id, 'mpd'), service_id,
                    mpd_id='dash', fatal=False))
                self._sort_formats(formats)
                info.update({
                    'id': service_id,
                    'display_id': video_id,
                    'formats': formats,
                })
        else:
            info.update({
                '_type': 'url_transparent',
                'url': service_id,
                'ie_key': service_name.capitalize(),
                'title': title,
            })
            if service_name == 'vimeo':
                info['url'] = smuggle_url(
                    'https://player.vimeo.com/video/' + service_id,
                    {'http_headers': {'Referer': url}})
        return info
