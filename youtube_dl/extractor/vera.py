# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VeraIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.vera\.com\.uy/canal/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://tv.vera.com.uy/canal/6001',
        'info_dict': {
            'id': '6001',
            'ext': 'mp4',
            'title': r're:^Vera\+ HD [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'md5:b3696ac8131004491079f61650856444',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        }
    }, {
        'url': 'http://tv.vera.com.uy/canal/6042',
        'info_dict': {
            'id': '6042',
            'ext': 'mp4',
            'title': r're:^Televisión Nacional [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'md5:91472413c939a91c45ad50f2d5ccf453',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        }
    }, {
        'url': 'http://tv.vera.com.uy/canal/6046',
        'info_dict': {
            'id': '6046',
            'ext': 'mp4',
            'title': r're:^TVCIUDAD [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'md5:aaee7e00ac0b0b1c04766f77fed6bbe9',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<h2 id="titulo_programa">(.+?)</h2>',
            webpage, 'title')
        description = self._html_search_regex(
            r'(?s)<p id="desc_programa">(.+?)</p>',
            webpage, 'description')
        thumbnail = self._html_search_regex(
            r'(?s)<div class="infoCanal">\s*<img src="(.+?)"',
            webpage, 'thumbnail')

        iframe_url = self._html_search_regex(
            r'#iframePlayerContent\'.*\'(http:\/\/.*extras.*)\'',
            webpage, 'iframe_url')

        iframe = self._download_webpage(iframe_url, video_id)
        playlist_url = self._html_search_regex(
            r'"source":{"hls": "(http:\/\/.*\.m3u8)"',
            iframe, 'playlist_url')

        formats = self._extract_m3u8_formats(playlist_url, video_id, 'mp4')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._live_title(title),
            'description': description,
            'thumbnail': thumbnail,
            'url': playlist_url,
            'formats': formats,
        }
