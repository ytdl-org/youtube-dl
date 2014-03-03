from __future__ import unicode_literals
import re

from .common import InfoExtractor


class Canal13clIE(InfoExtractor):
    _VALID_URL = r'^http://(?:www\.)?13\.cl/'
    IE_NAME = 'Canal13cl'

    def _real_extract(self, url):
        webpage = self._download_webpage(url, url)
        video_id = self._html_search_regex(
            r'http://streaming.13.cl/(.*)\.mp4',
            webpage, u'video_id')
        title = self._html_search_regex(
            r'(articuloTitulo = \"(.*?)\"|(.*?)\|)',
            webpage, u'title')
        url = self._html_search_regex(
            r'articuloVideo = \"(.*?)\"',
            webpage, u'url')
        thumbnail = self._html_search_regex (
            r'articuloImagen = \"(.*?)\"',
            webpage, u'thumbnail')

        return {
            'video_id': video_id,
            'url': url,
            'title': title,
            'ext': 'mp4',
            'thumbnail': thumbnail
        }
