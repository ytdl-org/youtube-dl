# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class SkypixelIE(InfoExtractor):
    """InfoExtractor for Skypixel.com"""

    _VALID_URL = r'https?://(?:www\.)?skypixel\.com/share/video/(?P<id>[^&#]+)'
    _TESTS = [
        {
            'url': 'https://skypixel.com/share/video/check-out-my-latest-artwork-4f90b8ac-e7c3-4ed8-82c2-203addfd629e',
            'info_dict': {
                'id': 'check-out-my-latest-artwork-4f90b8ac-e7c3-4ed8-82c2-203addfd629e',
                'ext': 'mp4',
                'title': 'Check out my latest artwork!',
                'uploader': 'Alby98',
                'thumbnail': 'http://dn-djidl2.qbox.me/cloud/c89382b0b8dc75ea9f07354e098e0971/2.jpg',
            },
            'params': {
                'noplaylist': True,
                'skip_download': True,
            }
        },
        {
            'url': 'https://www.skypixel.com/share/video/undirfellsrett-i-vatnsdal-8-9-2017',
            'info_dict': {
                'id': 'undirfellsrett-i-vatnsdal-8-9-2017',
                'ext': 'mp4',
                'title': 'Undirfellsrétt í Vatnsdal 8/9/2017',
                'uploader': 'Flokmundur',
                'thumbnail': 'http://dn-djidl2.qbox.me/cloud/3c1a3aea1bdc042362a36ed482edb3ae/2.jpg',
            },
            'params': {
                'noplaylist': True,
                'skip_download': True,
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage).strip()
        title = title.replace(' | SkyPixel.com', '')
        uploader = self._simple_search_between(
            webpage, u'<span itemprop="author">', u'</span>')
        assert(uploader is not None)
        djivideos_url = self._simple_search_between(
            webpage, u'<iframe frameborder="0" scrolling="no" src="', u'">')
        assert(djivideos_url is not None)
        djivideos_webpage = self._download_webpage(
            djivideos_url, 'djivideos.com[%s]' % (video_id, ))
        video_definitions_json = self._simple_search_between(
            djivideos_webpage, u'JSON.parse(\'', u'\');')
        assert(video_definitions_json is not None)
        video_definitions = self._parse_json(video_definitions_json, video_id)
        video_url = video_definitions[-1]['src']
        thumbnail = self._simple_search_between(
            djivideos_webpage, u'poster: "', u'",')
        if thumbnail is not None:
            url_params_start = thumbnail.find('?sign=')
            if url_params_start != -1:
                thumbnail = thumbnail[:url_params_start]

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'uploader': uploader,
            'thumbnail': thumbnail,
        }
