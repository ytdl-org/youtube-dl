from .common import InfoExtractor
from ..utils import (
    get_element_by_id,
    ExtractorError,
)

class ShahidIE(InfoExtractor):
    _VALID_URL = r'https?://shahid\.mbc\.net/ar/episode/(?P<id>\d+)/?'
    _TESTS = [
        {
            'url': 'https://shahid.mbc.net/ar/episode/108084/%D8%AE%D9%88%D8%A7%D8%B7%D8%B1-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%85-11-%D8%A7%D9%84%D8%AD%D9%84%D9%82%D8%A9-1.html',
            'info_dict': {
                'id': '108084',
                'ext': 'm3u8',
                'title': 'بسم الله',
                'description': 'بسم الله'
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            }
        },
        {
            #shahid plus subscriber only
            'url': 'https://shahid.mbc.net/ar/series/90497/%D9%85%D8%B1%D8%A7%D9%8A%D8%A7-2011.html',
            'only_matching': True
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        json_data = self._parse_json(
            get_element_by_id('jsonld', webpage),
            video_id
        )
        title = json_data['name']
        thumbnail = json_data.get('image')
        categories = json_data.get('genre')
        description = json_data.get('description')
        player_json_data = self._download_json(
            'https://shahid.mbc.net/arContent/getPlayerContent-param-.id-'+video_id+'.type-player.html',
            video_id
        )['data']
        if 'url' in player_json_data:
            m3u8_url = player_json_data['url']
        else:
            for error in json_data['error'].values():
                raise ExtractorError(error)
            return
        formats = self._extract_m3u8_formats(m3u8_url, video_id)
        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'categories': categories,
            'description': description,
            'formats': formats,
        }
