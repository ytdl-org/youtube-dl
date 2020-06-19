# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import url_or_none


class IDF1IE(InfoExtractor):
    IE_NAME = 'IDF1'
    _VALID_URL = r'https?://(?:www\.)?idf1\.fr/videos/(?:[^/|.]+)/(?P<id>[^/|.]+)\.html'
    _TESTS = [{
        'url': 'https://www.idf1.fr/videos/jlpp/2020-05-29-partie-1.html',
        'info_dict': {
            'id': '2020-05-29-partie-1',
            'ext': 'js',
            'title': 'JLPP - 2020/05/29 - partie 1 sur le replay IDF1 - IDF1',
            'description': '"Jacky lave plus propre, votre nouvelle &eacute;mission culte, tous les jours du lundi au vendredi &agrave; 17h00 sur IDF1&nbsp;!"',
            'url': 'https://player.dacast.com/js/player.js?contentId=15863_f_890022',
        },
    }, {
        'url': 'https://www.idf1.fr/videos/id-voyance/2020-03-13-partie-3.html',
        'info_dict': {
            'id': '2020-03-13-partie-3',
            'ext': 'js',
            'title': 'ID Voyance Île-de-France - 2020/03/13 - partie 3 sur le replay IDF1 - IDF1',
            'description': '"Isabelle et nos voyants en direct tous les vendredis d&egrave;s 20h50 sur IDF1 pour l\'&eacute;mission ID Voyance &Icirc;le-de-France."',
            'url': 'https://player.dacast.com/js/player.js?contentId=15863_f_827665',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title[^>]*>(.+?)</title>', webpage, 'title', default='(no title available)')
        description = self._html_search_regex(r'<meta[^>]*\sname=["|\']description["|\'][^>]*\scontent=(.+?)/>', webpage, 'description', fatal=False)
        dacast_link = self._html_search_regex(r'<script\ssrc=([^\>]+)></script>', webpage, 'link')
        dacast_link = url_or_none(dacast_link.replace('"', ''))
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'url': dacast_link,
        }
