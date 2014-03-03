from __future__ import unicode_literals
import re

from .common import InfoExtractor


class Canal13clIE(InfoExtractor):
    _VALID_URL = r'^http://(?:www\.)?13\.cl/programa/'
    IE_NAME = 'Canal13cl'

    def _real_extract(self, url):
        webpage = self._download_webpage(url)
        title = self._html_search_regex(
            r'articuloTitulo = \'(.*?)\'',
            webpage, u'title')
        url = self._html_search_regex(
            r'articuloVideo = \'(.*?)\'',
            webpage, u'url')
        thumbnail = self._html_search_regex (
            r'articuloImagen = \'(.*?)\'',
            webpage, u'thumbnail')

        return {
            'url': url,
            'title': title,
            'ext': 'mp4',
            'thumbnail': thumbnail
        }
