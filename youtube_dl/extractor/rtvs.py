# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    url_or_none,
    determine_ext
)


class RTVSIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rtvs\.sk/(?:radio|televizia)/archiv/\d+/(?P<id>\d+)'
    _TESTS = [{
        # radio archive
        'url': 'http://www.rtvs.sk/radio/archiv/11224/414872',
        'md5': '134d5d6debdeddf8a5d761cbc9edacb8',
        'info_dict': {
            'id': '414872',
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
            'id': '63118',
            'ext': 'mp4',
            'title': 'Amaro Džives - Náš deň',
            'description':
            'Galavečer pri príležitosti Medzinárodného dňa Rómov.'
        },
        'params': {
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        if url.find('/radio/') != -1:
            a2 = url.split('/')[-1]
            a1 = url.split('/')[-2]
            embed = self._download_webpage(
                "https://www.rtvs.sk/embed/radio/archive/%s/%s" % (a1, a2),
                video_id)
            audio_id = re.search('audio5f.json?id=(?P<id>[^\"]+)', embed)
            audio_id = audio_id.group('id')
            info = self._download_json(
                "https://www.rtvs.sk/json/audio5f.json?id=%s" % audio_id,
                audio_id)

            formats = []
            formats.append({
                'url': info['playlist'][0]['sources'][0]['src'],
                'format_id':  None,
                'height': 0
                })
            info = info['playlist'][0]
            return {
                'id': audio_id,
                'title': info.get('title'),
                'thumbnail': info.get('image'),
                'formats': formats
            }
        else:
            info = self._download_json(
                "https://www.rtvs.sk/json/archive5f.json?id=%s" % video_id,
                video_id)
            info = info.get('clip')

            formats = []
            for format_id, format_list in info.items():
                if not isinstance(format_list, list):
                    format_list = [format_list]
                for format_dict in format_list:
                    if not isinstance(format_dict, dict):
                        continue
                    format_url = url_or_none(format_dict.get('src'))
                    format_type = format_dict.get('type')
                    ext = determine_ext(format_url)
                    if (format_type == 'application/x-mpegURL'
                            or format_id == 'HLS' or ext == 'm3u8'):
                        formats.extend(self._extract_m3u8_formats(
                            format_url, video_id, 'mp4',
                            entry_protocol='m3u8_native', m3u8_id='hls',
                            fatal=False))
                    elif (format_type == 'application/dash+xml'
                          or format_id == 'DASH' or ext == 'mpd'):
                        pass
                    else:
                        formats.append({
                            'url': format_url,
                        })
            formats = sorted(formats, key=lambda i: i['tbr'])
            dt = info.get('datetime_create')
            return {
                'id': video_id,
                'title': info.get('title') + '-' + dt[:10],
                'thumbnail': info.get('image'),
                'description': info.get('description'),
                'formats': formats
            }
