# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class MelonVODIE(InfoExtractor):
    _VALID_URL = r'https?://vod\.melon\.com/video/detail2\.html?.*mvId=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://vod.melon.com/video/detail2.htm?mvId=50158734',
        'md5': '461fc04c6d23cbf49f4fef4d61851d32',
        'info_dict': {
            'id': '50158734',
            'ext': 'mp4',
            'title': 'Jessica \'Wonderland\' MV Making Film',
            'thumbnail': 're:^https?://.*\.jpg$',
            'artist': 'Jessica (제시카)',
            'upload_date': '20161212',
            'duration': 203,
        },
        'params': {
            'skip_download': 'm3u8 download',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        play_info = self._download_json(
            'http://vod.melon.com/video/playerInfo.json', video_id,
            note='Downloading playerInfo', query={'mvId': video_id}
        )
        title = play_info['mvInfo']['MVTITLE']
        artist = ', '.join([artist['ARTISTNAMEWEBLIST'] for artist in play_info.get('artistList', [])])

        info = self._download_json(
            'http://vod.melon.com/delivery/streamingInfo.json', video_id,
            note='Downloading streamingInfo',
            query={'contsId': video_id, 'contsType': 'VIDEO'}
        )
        stream_info = info.get('streamingInfo', {})
        m3u8_url = stream_info.get('encUrl')
        formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', m3u8_id='hls')
        self._sort_formats(formats)

        thumbnail = info.get('staticDomain', '') + stream_info.get('imgPath', '')
        duration = int_or_none(stream_info.get('playTime'))
        upload_date = stream_info.get('mvSvcOpenDt', '')[:8]

        return {
            'id': video_id,
            'title': title,
            'artist': artist,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'duration': duration,
            'formats': formats
        }