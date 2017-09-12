# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class DJIVideosIE(InfoExtractor):
    """InfoExtractor for djivideos.com"""

    _VALID_URL = r'https?://(?:www\.)?djivideos\.com/video_play/(?P<id>[^&#]+)'
    _TESTS = [
        {
            'url': 'https://www.djivideos.com/video_play/3d844cad-c722-4fdb-a270-a588d2ff6245',
            'info_dict': {
                'id': '3d844cad-c722-4fdb-a270-a588d2ff6245',
                # 'md5': 'b7d012bfd1a9a3bb5dbe0a3e32e48d28',
                'ext': 'mp4',
                'title': 'djivideos-3d844cad-c722-4fdb-a270-a588d2ff6245',
                'thumbnail': 'http://dn-djidl2.qbox.me/cloud/c89382b0b8dc75ea9f07354e098e0971/2.jpg',
            }
        },
        {
            'url': 'https://www.djivideos.com/video_play/02a59336-89bc-43f1-920d-40b24d96407a',
            'info_dict': {
                'id': '02a59336-89bc-43f1-920d-40b24d96407a',
                # 'md5': '7b2edcf58ddd0d14ef08bd73f8630929',
                'ext': 'mp4',
                'title': 'djivideos-02a59336-89bc-43f1-920d-40b24d96407a',
                'thumbnail': 'http://dn-djidl2.qbox.me/cloud/3c1a3aea1bdc042362a36ed482edb3ae/2.jpg',
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = 'djivideos-%s' % (video_id, )
        video_definitions_json = self._simple_search_between(
            webpage, u'JSON.parse(\'', u'\');')
        assert(video_definitions_json is not None)
        video_definitions = self._parse_json(video_definitions_json, video_id)
        video_url = video_definitions[-1]['src']
        video_url_params = video_url.find('?sign=')
        if video_url_params != -1:
            video_url = video_url[:video_url_params]
        thumbnail = self._simple_search_between(
            webpage, u'poster: "', u'",')
        if thumbnail is not None:
            url_params = thumbnail.find('?sign=')
            if url_params != -1:
                thumbnail = thumbnail[:url_params]

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'thumbnail': thumbnail,
        }
