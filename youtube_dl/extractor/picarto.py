# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError, js_to_json, urlencode_postdata


class PicartoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www.)?picarto\.tv/(?P<id>[a-zA-Z0-9]+)[^/]*$'
    _TEST = {
        'url': 'https://picarto.tv/Setz',
        'info_dict': {
            'id': 'Setz',
            'ext': 'mp4',
            'title': 're:^Setz [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'timestamp': int,
            'is_live': True
        },
        'params': {
            'skip_download': True
        }
    }

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        stream_page = self._download_webpage(url, channel_id)

        if 'This channel does not exist.' in stream_page:
            raise ExtractorError('Channel does not exist', expected=True)

        player_settings_js = self._html_search_regex(
            r'(?s)playerSettings\[1\]\s*=\s*(\{.+?\}\n)', stream_page, 'player-settings')
        player_settings = self._parse_json(player_settings_js, channel_id,
            transform_source=js_to_json)
        if not player_settings.get('online'):
            raise ExtractorError('Stream is offline', expected=True)

        cdn_data = self._download_json('https://picarto.tv/process/channel', channel_id,
            data=urlencode_postdata({'loadbalancinginfo': channel_id}),
            note='Fetching load balancer info')
        edge = [edge['ep'] for edge in cdn_data['edges'] if edge['id'] == cdn_data['preferedEdge']][0]

        formats = self._extract_m3u8_formats('https://%s/hls/%s/index.m3u8' % (edge, channel_id),
            channel_id, 'mp4')
        formats.append({'url': 'https://%s/mp4/%s.mp4' % (edge, channel_id)})
        self._sort_formats(formats)

        return {
            'id': channel_id,
            'formats': formats,
            'ext': 'mp4',
            'title': self._live_title(channel_id),
            'is_live': True,
            'thumbnail': player_settings.get('vodThumb'),
            'age_limit': 18 if player_settings.get('mature') else None,
        }


class PicartoVodIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www.)?picarto\.tv/videopopout/(?P<id>[a-zA-Z0-9_\-\.]+).flv'
    _TEST = {
        'url': 'https://picarto.tv/videopopout/Carrot_2018.01.11.07.55.12.flv',
        'md5': '80765b67813053ff31d4df2bd5e900ce',
        'info_dict': {
            'id': 'Carrot_2018.01.11.07.55.12',
            'ext': 'mp4',
            'title': 'Carrot_2018.01.11.07.55.12',
            'thumbnail': r're:^https?://.*\.jpg$'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        vod_info_js = self._html_search_regex(r'(?s)"#vod-player",\s*(\{.+?\})\)',
            webpage, video_id)
        vod_info = self._parse_json(vod_info_js, video_id, transform_source=js_to_json)

        return {
            'id': video_id,
            'title': video_id,
            'ext': 'mp4',
            'protocol': 'm3u8',
            'url': vod_info['vod'],
            'thumbnail': vod_info.get('vodThumb'),
        }
