from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import xpath_text

class GamekingsIE(InfoExtractor):
    _VALID_URL = r'http://www\.gamekings\.tv/videos/(?P<name>[0-9a-z\-]+)'
    _TESTS = [
        {
        'url': 'http://www.gamekings.tv/videos/phoenix-wright-ace-attorney-dual-destinies-review/',
        # MD5 is flaky, seems to change regularly
        # 'md5': '2f32b1f7b80fdc5cb616efb4f387f8a3',
        'info_dict': {
            'id': '20130811',
            'ext': 'mp4',
            'title': 'Phoenix Wright: Ace Attorney \u2013 Dual Destinies Review',
            'description': 'md5:36fd701e57e8c15ac8682a2374c99731',
            }
        },
        {
        'url': 'http://www.gamekings.tv/videos/the-legend-of-zelda-majoras-mask/',
        'info_dict': {
            'id': '118933752',
            'ext': 'mp4',
            'title': 'The Legend of Zelda: Majora’s Mask',
            'description': 'md5:9917825fe0e9f4057601fe1e38860de3'
            }
        }
    ]

    def _real_extract(self, url):

        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        webpage = self._download_webpage(url, name)

        playlist_id = re.search(r'(?:gogoVideo)\(\d+,"?(?P<playlist_id>.*)"', webpage, re.MULTILINE).group('playlist_id')
        playlist_url = 'http://www.gamekings.tv/wp-content/themes/gk2010/rss_playlist.php?id=' + playlist_id
        playlist_rss = self._download_xml(playlist_url, playlist_id)

        NS_MAP {
            'rss': 'http://rss.jwpcdn.com/'
         }

        # Todo: Implement Xpath for searching the video link
        
        video_url = self._og_search_video_url(webpage)

        video = re.search(r'[0-9]+', video_url)
        video_id = video.group(0)

        # Todo: add medium format
        video_url = video_url.replace(video_id, 'large/' + video_id)
        if "vimeo" in video_url:
            video_url = video_url.replace('large/' + video_id, video_id)
            video_url = video_url.replace('http://stream.gamekings.tv/', '')

        return {
            'id': video_id,
            'ext': 'mp4',
            'url': video_url,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
        }
