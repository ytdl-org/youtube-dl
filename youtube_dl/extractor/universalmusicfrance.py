# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..compat import (
    compat_urllib_request,
)

from ..utils import (
    urlencode_postdata,
)


class UniversalMusicFranceIE(InfoExtractor):
    _VALID_URL = r'https?://www\.universalmusic\.fr/artiste/.*/videos/(?P<id>.*)#?'
    _TESTS = [
        {
            'url': 'http://www.universalmusic.fr/artiste/7415-anna-bergendahl/videos/4555-for-you-remix-lyric-video.iframe',
            'md5': '159cda7568b9fc1e5e3de6aeca5d4bfc)',
            'info_dict': {
                'id': '1881-waiting-for-love-lyric-video',
                'ext': 'mp4',
                'title': '1881-waiting-for-love-lyric-video'
            }
        }
        ,
        {
            'url': 'https://www.universalmusic.fr/artiste/4428-avicii/videos/1881-waiting-for-love-lyric-video#contentPart',
            'md5': '159cda7568b9fc1e5e3de6aeca5d4bfc)',
            'info_dict': {
                'id': '1881-waiting-for-love-lyric-video',
                'ext': 'mp4',
                'title': '1881-waiting-for-love-lyric-video'
            }
        }
        ,
        {
            # from http://www.wat.tv/video/anna-bergendahl-for-you-2015-7dvjn_76lkz_.html
            'url': 'http://www.universalmusic.fr/artiste/7415-anna-bergendahl/videos/4555-for-you-remix-lyric-video',
            'md5': '159cda7568b9fc1e5e3de6aeca5d4bfc)',
            'info_dict': {
                'id': '4555-for-you-remix-lyric-video',
                'ext': 'mp4',
                'title': 'anna-bergendahl - for-you'
            }
        }
    ]
    GET_TOKEN_URL = 'http://www.universalmusic.fr/_/artiste/video/token'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        urlVideo = self._html_search_regex(r'var urlVideo = \'(.*)\';', webpage, 'urlVideo')
        title = self._html_search_regex(r'<meta\s*property="?og:title"?\s*content="(.*)"\s*/>', webpage, 'title')

        request = compat_urllib_request.Request(self.GET_TOKEN_URL, urlencode_postdata({'videoUrl': urlVideo}))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        request.add_header('X-Requested-With', 'XMLHttpRequest')
        manifest_json = self._download_webpage(request, None, note='Getting token', errnote='unable to get token')

        manifestUrl = self._parse_json(manifest_json, video_id).get("video")
        return {
            'id': video_id,
            'title': title,
            'description': title,
            'formats':
                self._extract_m3u8_formats(
                    manifestUrl, video_id, 'mp4')
        }
