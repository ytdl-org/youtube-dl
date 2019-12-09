# coding: utf-8
from __future__ import unicode_literals

import json
import re
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    int_or_none,
    js_to_json,
    merge_dicts,
)
class PokemonIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pokemon\.com/[a-z]{2}(?:.*?play=(?P<id>[a-z0-9]{32})|/(?:[^/]+/)+(?P<display_id>[^/?#&]+))'
    _TESTS = [{
        'url': 'https://www.pokemon.com/us/pokemon-episodes/20_30-the-ol-raise-and-switch/',
        'md5': '2fe8eaec69768b25ef898cda9c43062e',
        'info_dict': {
            'id': 'afe22e30f01c41f49d4f1d9eab5cd9a4',
            'ext': 'mp4',
            'title': 'The Ol’ Raise and Switch!',
            'description': 'md5:7db77f7107f98ba88401d3adc80ff7af',
            'timestamp': 1511824728,
            'upload_date': '20171127',
        },
        'add_id': ['LimelightMedia'],
    }]
    
    def _real_extract(self, url):
        video_id, display_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, video_id or display_id)
        video_data = extract_attributes(self._search_regex(
            r'(<[^>]+data-video-id="%s"[^>]*>)' % (video_id if video_id else '[a-z0-9]{32}'),
            webpage, 'video data element'))
        video_id = video_data['data-video-id']
        title = video_data.get('data-video-title') or self._html_search_meta(
            'pkm-title', webpage, ' title', default=None) or self._search_regex(
            r'<h1[^>]+\bclass=["\']us-title[^>]+>([^<]+)', webpage, 'title')
        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': 'limelight:media:%s' % video_id,
            'title': title,
            'description': video_data.get('data-video-summary'),
            'thumbnail': video_data.get('data-video-poster'),
            'series': 'Pokémon',
            'season_number': int_or_none(video_data.get('data-video-season')),
            'episode': title,
            'episode_number': int_or_none(video_data.get('data-video-episode')),
            'ie_key': 'LimelightMedia',
        }


class PokemonWatchIE(InfoExtractor):
    _VALID_URL = r'https?://watch\.pokemon\.com/[a-z]{2}-[a-z]{2}/player\.html\?id=(?P<id>[a-z0-9]{32})'
    _API_URL = 'https://www.pokemon.com/api/pokemontv/v2/channels/{0:}'
    _TESTS = []
    
    def _extract_media(self, channel_array, video_id):
        for channel in channel_array:
            for media in channel.get('media'):
                if media.get('id') == video_id:
                    return media
        return None
    
    def _real_extract(self, url):
        video_id = self._match_id(url)
        info = {
            '_type': 'url',
            'id': video_id,
            'url': 'limelight:media:%s' % video_id,
            'ie_key': 'LimelightMedia',
        }
        webpage = self._download_webpage(url, video_id)
        build_vars = self._parse_json(self._search_regex(
            r'(?s)buildVars\s*=\s*({.*?})', webpage, 'build vars'),
            video_id, transform_source=js_to_json)
        region = build_vars.get('region')
        channel_array = json.loads(
            self._download_webpage(self._API_URL.format(region), video_id))
        video_data = self._extract_media(channel_array, video_id)

        if video_data is None:
            raise ExtractorError(
                'Error', expected=True)

        info['_type'] = 'url_transparent'
        images = video_data.get('images')
        return merge_dicts(info, {
            'title': video_data.get('title'),
            'description': video_data.get('description'),
            'thumbnail': images.get('medium') or images.get('small'),
            'series': 'Pokémon',
            'season_number': int_or_none(video_data.get('season')),
            'episode': video_data.get('title'),
            'episode_number': int_or_none(video_data.get('episode')),
        })
