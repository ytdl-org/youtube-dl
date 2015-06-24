from .common import InfoExtractor

class ShahidIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?shahid\.mbc\.net/ar/episode/(?P<id>\d+)/?'
    _TESTS = [
        {
            'url': 'https://shahid.mbc.net/ar/episode/108084/%D8%AE%D9%88%D8%A7%D8%B7%D8%B1-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%85-11-%D8%A7%D9%84%D8%AD%D9%84%D9%82%D8%A9-1.html',
            'info_dict': {
                'id': '108084',
                'ext': 'm3u8',
                'title': 'بسم الله',
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
        title = self._og_search_title(webpage);
        json_data = self._download_json(
            'https://shahid.mbc.net/arContent/getPlayerContent-param-.id-'+video_id+'.type-player.html',
            video_id
        )['data']
        if 'url' in json_data:
            m3u8_url = json_data['url']
        else:
            for error in json_data['error'].values():
                self.report_warning(error)
            return
        formats = self._extract_m3u8_formats(m3u8_url, video_id)
        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }