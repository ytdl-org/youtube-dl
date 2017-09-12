# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class SkypixelIE(InfoExtractor):
    """InfoExtractor for skypixel.com (generic embed for djivideos)"""

    _VALID_URL = r'https?://(?:www\.)?skypixel\.com/share/video/(?P<id>[^&#]+)'
    _TESTS = [
        {
            'url': 'https://skypixel.com/share/video/check-out-my-latest-artwork-4f90b8ac-e7c3-4ed8-82c2-203addfd629e',
            'info_dict': {
                'id': '3d844cad-c722-4fdb-a270-a588d2ff6245',
                'url': 'http://dn-djidl2.qbox.me/cloud/c89382b0b8dc75ea9f07354e098e0971/720.mp4',
                'ext': 'mp4',
                'title': 'Check out my latest artwork!',
                'uploader': 'Alby98',
            },
            'params': {
                'skip_download': True,
            }
        },
        {
            'url': 'https://www.skypixel.com/share/video/undirfellsrett-i-vatnsdal-8-9-2017',
            'info_dict': {
                'id': '02a59336-89bc-43f1-920d-40b24d96407a',
                'url': 'http://dn-djidl2.qbox.me/cloud/3c1a3aea1bdc042362a36ed482edb3ae/1080.mp4',
                'ext': 'mp4',
                'title': 'Undirfellsrétt í Vatnsdal 8/9/2017',
                'uploader': 'Flokmundur',
            },
            'params': {
                'skip_download': True,
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage).strip().replace(' | SkyPixel.com', '')
        uploader = self._simple_search_between(
            webpage, u'<span itemprop="author">', u'</span>')
        url = self._simple_search_between(
            webpage, u'<iframe frameborder="0" scrolling="no" src="', u'">')
        assert(url is not None)
        url_params = url.find('?autoplay=')
        if url_params != -1:
            url = url[:url_params]

        return {
            '_type': 'url_transparent',
            'ie_key': 'DJIVideos',
            'id': video_id,
            'url': url,
            'ext': 'mp4',
            'title': title,
            'uploader': uploader
        }
