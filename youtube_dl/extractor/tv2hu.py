# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

class TV2HUIE(InfoExtractor):
    IE_NAME = 'tv2.hu'
    _VALID_URL = r'https?://(?:www\.)?tv2\.hu/(?:musoraink/)?(?P<uploader>[^/]+)/(?:teljes_adasok/)?(?P<id>[0-9]+)_(.+?)\.html'
    _JSON_URL = r'(?P<json_url>https?://.+?\.tv2\.hu/vod/(?P<upload_date>\d+)/id_(?P<upload_id>\d+).+?&type=json)'
    
    _TESTS = [{
        'url': 'http://tv2.hu/ezek_megorultek/217679_ezek-megorultek---1.-adas-1.-resz.html',
        'info_dict': {
            'id': '217679',
            'ext': 'mp4',
            'title': 'Ezek megőrültek! - 1. adás 1. rész',
            'upload_id': '220289',
            'upload_date': '20160826',
            'uploader': 'ezek_megorultek',
            'thumbnail': 're:^https?://.*\.jpg$'
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        'url': 'http://tv2.hu/ezek_megorultek/teljes_adasok/217677_ezek-megorultek---1.-adas-2.-resz.html',
        'info_dict': {
            'id': '217677',
            'ext': 'mp4',
            'title': 'Ezek megőrültek! - 1. adás 2. rész',
            'upload_id': '220290',
            'upload_date': '20160826',
            'uploader': 'ezek_megorultek',
            'thumbnail': 're:^https?://.*\.jpg$'
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        'url': 'http://tv2.hu/musoraink/aktiv/aktiv_teljes_adas/217963_aktiv-teljes-adas---2016.08.30..html',
        'info_dict': {
            'id': '217963',
            'ext': 'mp4',
            'title': 'AKTÍV / Aktív teljes adás - 2016.08.30. / tv2.hu',
            'upload_id': '220700',
            'upload_date': '20160830',
            'uploader': 'aktiv',
            'thumbnail': 're:^https?://.*\.jpg$'
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            url, video_id, 'Downloading info page')

        json_url = re.search(self._JSON_URL, webpage)

        json_data = self._download_json(
            json_url.group('json_url'), video_id, 'Downloading video info')

        manifest_url = json_data['bitrates']['hls']

        formats = self._extract_m3u8_formats(
            manifest_url, video_id, 'mp4', entry_protocol='m3u8_native')

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage).strip(),
            'thumbnail': self._og_search_property('image', webpage),
            'uploader': self._search_regex(self._VALID_URL, url, 'uploader'),
            'upload_id': json_url.group('upload_id'),
            'upload_date': json_url.group('upload_date'),
            'formats': formats
        }