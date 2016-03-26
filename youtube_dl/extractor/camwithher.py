from __future__ import unicode_literals

from .common import InfoExtractor


class CamWithHerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?camwithher\.tv/view_video\.php\?viewkey=*'

    _TESTS = [
        {
            'url': 'http://camwithher.tv/view_video.php?viewkey=6e9a24e2c0e842e1f177&page=&viewtype=&category=',
            'info_dict': {
                'id': '5644',
                'ext': 'mp4',
                'title': 'Periscope Tease',
            },
            'params': {
                'skip_download': True,
            }
        },
        {
            'url': 'http://camwithher.tv/view_video.php?viewkey=6dfd8b7c97531a459937',
            'only_matching': True,
        },
        {
            'url': 'http://camwithher.tv/view_video.php?viewkey=b6c3b5bea9515d1a1fc4&page=&viewtype=&category=mv',
            'info_dict': {
                'id': '758',
                'ext': 'flv',
                'title': 'Gisele in the Bath',
            },
            'params': {
                'skip_download': True,
            }
        },
    ]

    def _real_extract(self, url):
        url = self._download_webpage(url, '')

        video_id = self._html_search_regex(r'<a href="/download/\?v=(.+?)\.', url, 'id')

        if int(video_id) > 2010:
            rtmp_url = 'rtmp://camwithher.tv/clipshare/mp4:' + video_id + '.mp4'
            ext = 'mp4'
        else:
            rtmp_url = 'rtmp://camwithher.tv/clipshare/' + video_id
            ext = 'flv'

        title = self._html_search_regex(r'<div style="float:left">\s+<h2>(.+?)</h2>', url, 'title')

        return {
            'id': video_id,
            'url': rtmp_url,
            'no_resume': True,
            'ext': ext,
            'title': title,
        }
