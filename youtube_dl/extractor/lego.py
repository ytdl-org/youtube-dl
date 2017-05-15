# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    unescapeHTML,
    parse_duration,
    get_element_by_class,
)


class LEGOIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?lego\.com/(?P<locale>[^/]+)/(?:[^/]+/)*videos/(?:[^/]+/)*[^/?#]+-(?P<id>[0-9a-f]+)'
    _TESTS = [{
        'url': 'http://www.lego.com/en-us/videos/themes/club/blocumentary-kawaguchi-55492d823b1b4d5e985787fa8c2973b1',
        'md5': 'f34468f176cfd76488767fc162c405fa',
        'info_dict': {
            'id': '55492d823b1b4d5e985787fa8c2973b1',
            'ext': 'mp4',
            'title': 'Blocumentary Great Creations: Akiyuki Kawaguchi',
            'description': 'Blocumentary Great Creations: Akiyuki Kawaguchi',
        },
    }, {
        # geo-restricted but the contentUrl contain a valid url
        'url': 'http://www.lego.com/nl-nl/videos/themes/nexoknights/episode-20-kingdom-of-heroes-13bdc2299ab24d9685701a915b3d71e7##sp=399',
        'md5': '4c3fec48a12e40c6e5995abc3d36cc2e',
        'info_dict': {
            'id': '13bdc2299ab24d9685701a915b3d71e7',
            'ext': 'mp4',
            'title': 'Aflevering 20 - Helden van het koninkrijk',
            'description': 'md5:8ee499aac26d7fa8bcb0cedb7f9c3941',
        },
    }, {
        # special characters in title
        'url': 'http://www.lego.com/en-us/starwars/videos/lego-star-wars-force-surprise-9685ee9d12e84ff38e84b4e3d0db533d',
        'info_dict': {
            'id': '9685ee9d12e84ff38e84b4e3d0db533d',
            'ext': 'mp4',
            'title': 'Force Surprise – LEGO® Star Wars™ Microfighters',
            'description': 'md5:9c673c96ce6f6271b88563fe9dc56de3',
        },
        'params': {
            'skip_download': True,
        },
    }]
    _BITRATES = [256, 512, 1024, 1536, 2560]

    def _real_extract(self, url):
        locale, video_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, video_id)
        title = get_element_by_class('video-header', webpage).strip()
        progressive_base = 'https://lc-mediaplayerns-live-s.legocdn.com/'
        streaming_base = 'http://legoprod-f.akamaihd.net/'
        content_url = self._html_search_meta('contentUrl', webpage)
        path = self._search_regex(
            r'(?:https?:)?//[^/]+/(?:[iz]/s/)?public/(.+)_[0-9,]+\.(?:mp4|webm)',
            content_url, 'video path', default=None)
        if not path:
            player_url = self._proto_relative_url(self._search_regex(
                r'<iframe[^>]+src="((?:https?)?//(?:www\.)?lego\.com/[^/]+/mediaplayer/video/[^"]+)',
                webpage, 'player url', default=None))
            if not player_url:
                base_url = self._proto_relative_url(self._search_regex(
                    r'data-baseurl="([^"]+)"', webpage, 'base url',
                    default='http://www.lego.com/%s/mediaplayer/video/' % locale))
                player_url = base_url + video_id
            player_webpage = self._download_webpage(player_url, video_id)
            video_data = self._parse_json(unescapeHTML(self._search_regex(
                r"video='([^']+)'", player_webpage, 'video data')), video_id)
            progressive_base = self._search_regex(
                r'data-video-progressive-url="([^"]+)"',
                player_webpage, 'progressive base', default='https://lc-mediaplayerns-live-s.legocdn.com/')
            streaming_base = self._search_regex(
                r'data-video-streaming-url="([^"]+)"',
                player_webpage, 'streaming base', default='http://legoprod-f.akamaihd.net/')
            item_id = video_data['ItemId']

            net_storage_path = video_data.get('NetStoragePath') or '/'.join([item_id[:2], item_id[2:4]])
            base_path = '_'.join([item_id, video_data['VideoId'], video_data['Locale'], compat_str(video_data['VideoVersion'])])
            path = '/'.join([net_storage_path, base_path])
        streaming_path = ','.join(map(lambda bitrate: compat_str(bitrate), self._BITRATES))

        formats = self._extract_akamai_formats(
            '%si/s/public/%s_,%s,.mp4.csmil/master.m3u8' % (streaming_base, path, streaming_path), video_id)
        m3u8_formats = list(filter(
            lambda f: f.get('protocol') == 'm3u8_native' and f.get('vcodec') != 'none',
            formats))
        if len(m3u8_formats) == len(self._BITRATES):
            self._sort_formats(m3u8_formats)
            for bitrate, m3u8_format in zip(self._BITRATES, m3u8_formats):
                progressive_base_url = '%spublic/%s_%d.' % (progressive_base, path, bitrate)
                mp4_f = m3u8_format.copy()
                mp4_f.update({
                    'url': progressive_base_url + 'mp4',
                    'format_id': m3u8_format['format_id'].replace('hls', 'mp4'),
                    'protocol': 'http',
                })
                web_f = {
                    'url': progressive_base_url + 'webm',
                    'format_id': m3u8_format['format_id'].replace('hls', 'webm'),
                    'width': m3u8_format['width'],
                    'height': m3u8_format['height'],
                    'tbr': m3u8_format.get('tbr'),
                    'ext': 'webm',
                }
                formats.extend([web_f, mp4_f])
        else:
            for bitrate in self._BITRATES:
                for ext in ('web', 'mp4'):
                    formats.append({
                        'format_id': '%s-%s' % (ext, bitrate),
                        'url': '%spublic/%s_%d.%s' % (progressive_base, path, bitrate, ext),
                        'tbr': bitrate,
                        'ext': ext,
                    })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': self._html_search_meta('description', webpage),
            'thumbnail': self._html_search_meta('thumbnail', webpage),
            'duration': parse_duration(self._html_search_meta('duration', webpage)),
            'formats': formats,
        }
