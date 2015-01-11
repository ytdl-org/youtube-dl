from __future__ import unicode_literals

from .common import InfoExtractor
from .common import ExtractorError
from ..utils import parse_iso8601
import json
import re

class DRBonanzaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dr\.dk/bonanza/(?:[^/]+/)+(?:[^/])+?(?:assetId=(?P<id>\d+))?(?:[#&]|$)'

    _TESTS = [{
        'url': 'http://www.dr.dk/bonanza/serie/portraetter/Talkshowet.htm?assetId=65517',
        'md5': 'fe330252ddea607635cf2eb2c99a0af3',
        'info_dict': {
            'id': '65517',
            'ext': 'mp4',
            'title': 'Talkshowet - Leonard Cohen',
            'description': 'md5:8f34194fb30cd8c8a30ad8b27b70c0ca',
            'timestamp': 1295537932,
            'upload_date': '20110120',
            'duration': 3664000,
        },
    },{
        'url': 'http://www.dr.dk/bonanza/radio/serie/sport/fodbold.htm?assetId=59410',
        'md5': '6dfe039417e76795fb783c52da3de11d',
        'info_dict': {
            'id': '59410',
            'ext': 'mp3',
            'title': 'EM fodbold 1992 Danmark - Tyskland finale Transmission',
            'description': 'md5:501e5a195749480552e214fbbed16c4e',
            'timestamp': 1223274900,
            'upload_date': '20081006',
            'duration': 7369000,
        },
    }]

    def _real_extract(self, url):
        url_id = self._match_id(url)
        
        webpage = self._download_webpage(url, url_id if url_id else "")
        
        if url_id:
            info = json.loads(self._html_search_regex(r'({.*?' + url_id + '.*})', webpage, 'json'))
        else:
            # Just fetch the first video on that page
            info = json.loads(self._html_search_regex(r'bonanzaFunctions.newPlaylist\(({.*})\)', webpage, 'json'))
        
        asset_id = str(info['AssetId'])
        title = info['Title'].rstrip(' \'\"-,.:;!?')
        duration = info['Duration']
        timestamp = parse_iso8601(re.sub(r'\.\d+$', '', info['Created'])) # First published online. "FirstPublished" contains the date for original airing.
        
        def parse_filename_info(url):
            match = re.search(r'/\d+_(?P<width>\d+)x(?P<height>\d+)x(?P<bitrate>\d+)K\.(?P<ext>\w+)$', url)
            if match:
                return {'width': int(match.group(1)), 'height': int(match.group(2)), 'bitrate': int(match.group(3)), 'ext': match.group(4)}
            match = re.search(r'/\d+_(?P<bitrate>\d+)K\.(?P<ext>\w+)$', url)
            if match:
                return {'bitrate': int(match.group(1)), 'ext': match.group(2)}
            return {'width': None, 'height': None, 'bitrate': None, 'ext': None}
        
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
                    fileinfo = parse_filename_info(file['Location'])
                    formats.append({
                        'url': file['Location'],
                        'format_id': file['Type'].replace('Video', ''),
                        'preference': preferencemap.get(file['Type'], -10),
                        'width': fileinfo['width'],
                        'height': fileinfo['height'],
                        'vbr': fileinfo['bitrate'],
                        'ext': fileinfo['ext'],
                    })
                elif file['Type'] == "Thumb":
                    thumbnail = file['Location']
            elif info['Type'] == "Audio":
                if file['Type'] == "Audio":
                    fileinfo = parse_filename_info(file['Location'])
                    formats.append({
                        'url': file['Location'],
                        'format_id': file['Type'],
                        'abr': fileinfo['bitrate'],
                        'ext': fileinfo['ext'],
                        'vcodec': 'none',
                    })
                elif file['Type'] == "Thumb":
                    thumbnail = file['Location']
        
        description = "{}\n{}\n{}\n".format(info['Description'], info['Actors'], info['Colophon'])

        for f in formats:
            f['url'] = f['url'].replace('rtmp://vod-bonanza.gss.dr.dk/bonanza/', 'http://vodfiles.dr.dk/')
            f['url'] = f['url'].replace('mp4:bonanza', 'bonanza')
        
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
