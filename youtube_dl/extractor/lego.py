# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    unescapeHTML,
    int_or_none,
)


class LEGOIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?lego\.com/(?:[^/]+/)*videos/(?:[^/]+/)*[^/?#]+-(?P<id>[0-9a-f]+)'
    _TEST = {
        'url': 'http://www.lego.com/en-us/videos/themes/club/blocumentary-kawaguchi-55492d823b1b4d5e985787fa8c2973b1',
        'md5': 'f34468f176cfd76488767fc162c405fa',
        'info_dict': {
            'id': '55492d823b1b4d5e985787fa8c2973b1',
            'ext': 'mp4',
            'title': 'Blocumentary Great Creations: Akiyuki Kawaguchi',
        }
    }
    _BITRATES = [256, 512, 1024, 1536, 2560]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            'http://www.lego.com/en-US/mediaplayer/video/' + video_id, video_id)
        title = self._search_regex(r'<title>(.+?)</title>', webpage, 'title')
        video_data = self._parse_json(unescapeHTML(self._search_regex(
            r"video='([^']+)'", webpage, 'video data')), video_id)
        progressive_base = self._search_regex(
            r'data-video-progressive-url="([^"]+)"',
            webpage, 'progressive base', default='https://lc-mediaplayerns-live-s.legocdn.com/')
        streaming_base = self._search_regex(
            r'data-video-streaming-url="([^"]+)"',
            webpage, 'streaming base', default='http://legoprod-f.akamaihd.net/')
        item_id = video_data['ItemId']

        net_storage_path = video_data.get('NetStoragePath') or '/'.join([item_id[:2], item_id[2:4]])
        base_path = '_'.join([item_id, video_data['VideoId'], video_data['Locale'], compat_str(video_data['VideoVersion'])])
        path = '/'.join([net_storage_path, base_path])
        streaming_path = ','.join(map(lambda bitrate: compat_str(bitrate), self._BITRATES))

        formats = self._extract_akamai_formats(
            '%si/s/public/%s_,%s,.mp4.csmil/master.m3u8' % (streaming_base, path, streaming_path), video_id)
        m3u8_formats = list(filter(
            lambda f: f.get('protocol') == 'm3u8_native' and f.get('vcodec') != 'none' and f.get('resolution') != 'multiple',
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
            'thumbnail': video_data.get('CoverImageUrl'),
            'duration': int_or_none(video_data.get('Length')),
            'formats': formats,
        }
