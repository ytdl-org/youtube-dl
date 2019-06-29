# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import determine_ext


class RTVSIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rtvs\.sk/(?:radio|televizia)/archiv/\d+/(?P<id>\d+)'
    _TESTS = [{
        # radio archive
        'url': 'http://www.rtvs.sk/radio/archiv/11224/414872',
        'md5': '134d5d6debdeddf8a5d761cbc9edacb8',
        'info_dict': {
            'id': '135320',
            'ext': 'mp3',
            'title': 'Ostrov pokladov 1 časť.mp3'
        },
        'params': {
            'skip_download': True,
        }
    }, {
        # tv archive
        'url': 'http://www.rtvs.sk/televizia/archiv/8249/63118',
        'md5': '85e2c55cf988403b70cac24f5c086dc6',
        'info_dict': {
            'id': '17189',
            'ext': 'mp4',
            'title': 'Amaro Džives - Náš deň',
            'description': 'Galavečer pri príležitosti Medzinárodného dňa Rómov.'
        },
        'params': {
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        playlist_url = self._search_regex(
            r'url = (["\'])(?:https?:)?(?://)(?P<url>(?:(?!\1).)+)\1', webpage,
            'playlist url', group='url')

        if not playlist_url.startswith("http"):
            playlist_url = "http://" + playlist_url

        data = self._download_json(
            playlist_url, video_id, 'Downloading playlist')

        try:
            data_media = data['clip']
        except KeyError:
            data_media = data['playlist'][0]

        media_id = data_media['mediaid']
        title = data_media['title']
        description = data_media.get('description')
        thumbnail = data_media.get('image')

        info = {
            'id': media_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }

        url = data_media['sources'][0]['src']

        if determine_ext(url) == 'm3u8':
            info['formats'] = self._extract_m3u8_formats(
                url, video_id, 'mp4',
                entry_protocol='m3u8_native', m3u8_id='hls')
        else:
            info['url'] = url

        return info
