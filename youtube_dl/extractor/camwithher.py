from __future__ import unicode_literals

from .common import InfoExtractor


class CamWithHerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?camwithher\.tv/view_video\.php\?.*viewkey=(?P<id>\w+)'

    _TESTS = [
        {
            'url': 'http://camwithher.tv/view_video.php?viewkey=6e9a24e2c0e842e1f177&page=&viewtype=&category=',
            'info_dict': {
                'id': '5644',
                'ext': 'flv',
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
            'url': 'http://camwithher.tv/view_video.php?page=&viewkey=6e9a24e2c0e842e1f177&viewtype=&category=',
            'only_matching': True,
        },
        {
            'url': 'http://camwithher.tv/view_video.php?viewkey=b6c3b5bea9515d1a1fc4&page=&viewtype=&category=mv',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        flv_id = self._html_search_regex(r'<a href="/download/\?v=(\d+)', webpage, 'id')

        # The number "2010" was reverse-engineered from cwhplayer.swf.
        # It appears that they changed their video codec, and hence the RTMP URL
        # scheme at that video's ID.
        rtmp_url = 'rtmp://camwithher.tv/clipshare/%s' % (('mp4:%s.mp4' % flv_id) if int(flv_id) > 2010 else flv_id)

        title = self._html_search_regex(r'<div style="float:left">\s+<h2>(.+?)</h2>', webpage, 'title')

        return {
            'id': flv_id,
            'url': rtmp_url,
            'no_resume': True,
            'ext': 'flv',
            'title': title,
        }
