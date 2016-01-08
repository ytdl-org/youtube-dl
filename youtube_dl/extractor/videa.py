# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
)

class VideaIE(InfoExtractor):
    _VALID_URL = r'https?://videa\.hu/videok/(.+?)/?(?P<id>\d+)'
    IE_NAME = 'videa.hu'

    _TEST = {
        'url': 'http://videa.hu/videok/kreativ/igy-lehet-nekimenni-a-hosegnek-ballon-hoseg-CZqIVSVYfJKf9bHC',
        'md5': 'e9a24350bbd485746d23519319949e72',
        'info_dict': {
            'id': 'CZqIVSVYfJKf9bHC',
            'ext': '1150387',
            'title': 'Így lehet nekimenni a hőségnek',
            'description': '',
            'uploader': 'viktoratakarító',
        } 
    }

    def _real_extract(self, url):

        # the last part of the slug is the real video hash id
        video_id = self._search_regex(r'([A-Za-z0-9]+)$', url, 'video id')

        info_data = compat_urllib_parse.urlencode({
            'format': 'json',
            'url': url,
        })

        # access the oembed data for video infos
        info = self._download_json(
            'http://videa.hu/oembed/?url=%s&format=json' % info_data, url, 'Downloading video info')

        # get the player xmldata for the video file url 
        flvplayer = self._download_xml(
            'http://videa.hu/flvplayer_get_video_xml.php?v=%s' %  video_id, 'Downloading player datas')
        
        duration = flvplayer.find('./video/duration').text;
        values = flvplayer.find('./video/versions').text;
        for elem in flvplayer.findall('video/versions/version'):
            video_url = elem.get('video_url')

        return {
            'id': video_id,
            'title': info['title'],
            'url': video_url,
            'thumbnail': info['thumbnail_url'],
            'description': '',
            'uploader': info['author_name'],
        }