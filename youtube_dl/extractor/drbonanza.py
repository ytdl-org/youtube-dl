from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
)


class DRBonanzaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dr\.dk/bonanza/(?:[^/]+/)+(?:[^/])+?(?:assetId=(?P<id>\d+))?(?:[#&]|$)'

    _TESTS = [{
        'url': 'http://www.dr.dk/bonanza/serie/portraetter/Talkshowet.htm?assetId=65517',
        'info_dict': {
            'id': '65517',
            'ext': 'mp4',
            'title': 'Talkshowet - Leonard Cohen',
            'description': 'md5:8f34194fb30cd8c8a30ad8b27b70c0ca',
            'thumbnail': 're:^https?://.*\.(?:gif|jpg)$',
            'timestamp': 1295537932,
            'upload_date': '20110120',
            'duration': 3664,
        },
        'params': {
            'skip_download': True,  # requires rtmp
        },
    }, {
        'url': 'http://www.dr.dk/bonanza/radio/serie/sport/fodbold.htm?assetId=59410',
        'md5': '6dfe039417e76795fb783c52da3de11d',
        'info_dict': {
            'id': '59410',
            'ext': 'mp3',
            'title': 'EM fodbold 1992 Danmark - Tyskland finale Transmission',
            'description': 'md5:501e5a195749480552e214fbbed16c4e',
            'thumbnail': 're:^https?://.*\.(?:gif|jpg)$',
            'timestamp': 1223274900,
            'upload_date': '20081006',
            'duration': 7369,
        },
    }]

    def _real_extract(self, url):
        url_id = self._match_id(url)
        webpage = self._download_webpage(url, url_id)

        if url_id:
            info = json.loads(self._html_search_regex(r'({.*?%s.*})' % url_id, webpage, 'json'))
        else:
            # Just fetch the first video on that page
            info = json.loads(self._html_search_regex(r'bonanzaFunctions.newPlaylist\(({.*})\)', webpage, 'json'))

        asset_id = str(info['AssetId'])
        title = info['Title'].rstrip(' \'\"-,.:;!?')
        duration = int_or_none(info.get('Duration'), scale=1000)
        # First published online. "FirstPublished" contains the date for original airing.
        timestamp = parse_iso8601(
            re.sub(r'\.\d+$', '', info['Created']))

        def parse_filename_info(url):
            match = re.search(r'/\d+_(?P<width>\d+)x(?P<height>\d+)x(?P<bitrate>\d+)K\.(?P<ext>\w+)$', url)
            if match:
                return {
                    'width': int(match.group('width')),
                    'height': int(match.group('height')),
                    'vbr': int(match.group('bitrate')),
                    'ext': match.group('ext')
                }
            match = re.search(r'/\d+_(?P<bitrate>\d+)K\.(?P<ext>\w+)$', url)
            if match:
                return {
                    'vbr': int(match.group('bitrate')),
                    'ext': match.group(2)
                }
            return {}

        video_types = ['VideoHigh', 'VideoMid', 'VideoLow']
        preferencemap = {
            'VideoHigh': -1,
            'VideoMid': -2,
            'VideoLow': -3,
            'Audio': -4,
        }

        formats = []
        for file in info['Files']:
            if info['Type'] == "Video":
                if file['Type'] in video_types:
                    format = parse_filename_info(file['Location'])
                    format.update({
                        'url': file['Location'],
                        'format_id': file['Type'].replace('Video', ''),
                        'preference': preferencemap.get(file['Type'], -10),
                    })
                    if format['url'].startswith('rtmp'):
                        rtmp_url = format['url']
                        format['rtmp_live'] = True  # --resume does not work
                        if '/bonanza/' in rtmp_url:
                            format['play_path'] = rtmp_url.split('/bonanza/')[1]
                    formats.append(format)
                elif file['Type'] == "Thumb":
                    thumbnail = file['Location']
            elif info['Type'] == "Audio":
                if file['Type'] == "Audio":
                    format = parse_filename_info(file['Location'])
                    format.update({
                        'url': file['Location'],
                        'format_id': file['Type'],
                        'vcodec': 'none',
                    })
                    formats.append(format)
                elif file['Type'] == "Thumb":
                    thumbnail = file['Location']

        description = '%s\n%s\n%s\n' % (
            info['Description'], info['Actors'], info['Colophon'])

        self._sort_formats(formats)

        display_id = re.sub(r'[^\w\d-]', '', re.sub(r' ', '-', title.lower())) + '-' + asset_id
        display_id = re.sub(r'-+', '-', display_id)

        return {
            'id': asset_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
        }
