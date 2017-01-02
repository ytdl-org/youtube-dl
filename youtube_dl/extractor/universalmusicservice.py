# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
import base64

class UniversalMusicServiceIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?universal-music.de\/.+video:(?P<id>[0-9]+)\/'
    _TEST = {
        'url': 'http://www.universal-music.de/sido/videos/detail/video:373201/astronaut',
        'md5': 'f32cf902b8ab711bd2e5a9baac84af84',
        'info_dict': {
            'id': '373201',
            'ext': 'mp4',
            'title': 'Astronaut'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_url = "http://mediadelivery.universal-music-services.de/vod/mp4:autofill/storage/" + video_id[0:1] + "/" + video_id[1:2] + "/" + video_id[2:3] + "/" + video_id[3:4] + "/" + video_id[4:5] + "/" + video_id[5:6] + "/content/836/file/playlist.m3u8"
        #video_url = "http://mediadelivery.universal-music-services.de/vod/mp4:autofill/storage/" + video_id[0:1] + "/" + video_id[1:2] + "/" + video_id[2:3] + "/" + video_id[3:4] + "/" + video_id[4:5] + "/" + video_id[5:6] + "/content/686/file/playlist.m3u8"

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>.+ \| (.+) \| .+<\/title>', webpage, 'title')
        album = self._html_search_regex(r'class="product-banner-text1">(.+)<\/p>', webpage, 'album')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'album': album,
            'ext': 'mp4'
        }


