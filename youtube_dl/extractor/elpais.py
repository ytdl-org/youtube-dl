# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import unified_strdate


class ElPaisIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^.]+\.)?elpais\.com/.*/(?P<id>[^/#?]+)\.html(?:$|[?#])'
    IE_DESC = 'El País'

    _TEST = {
        'url': 'http://blogs.elpais.com/la-voz-de-inaki/2014/02/tiempo-nuevo-recetas-viejas.html',
        'md5': '98406f301f19562170ec071b83433d55',
        'info_dict': {
            'id': 'tiempo-nuevo-recetas-viejas',
            'ext': 'mp4',
            'title': 'Tiempo nuevo, recetas viejas',
            'description': 'De lunes a viernes, a partir de las ocho de la mañana, Iñaki Gabilondo nos cuenta su visión de la actualidad nacional e internacional.',
            'upload_date': '20140206',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        prefix = self._html_search_regex(
            r'var url_cache = "([^"]+)";', webpage, 'URL prefix')
        video_suffix = self._search_regex(
            r"URLMediaFile = url_cache \+ '([^']+)'", webpage, 'video URL')
        video_url = prefix + video_suffix
        thumbnail_suffix = self._search_regex(
            r"URLMediaStill = url_cache \+ '([^']+)'", webpage, 'thumbnail URL',
            fatal=False)
        thumbnail = (
            None if thumbnail_suffix is None
            else prefix + thumbnail_suffix)
        title = self._html_search_regex(
            '<h2 class="entry-header entry-title.*?>(.*?)</h2>',
            webpage, 'title')
        date_str = self._search_regex(
            r'<p class="date-header date-int updated"\s+title="([^"]+)">',
            webpage, 'upload date', fatal=False)
        upload_date = (None if date_str is None else unified_strdate(date_str))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': thumbnail,
            'upload_date': upload_date,
        }
