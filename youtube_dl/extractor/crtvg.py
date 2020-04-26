
# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unescapeHTML,
    unified_strdate,
)


class CRTVGIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?crtvg\.(?:gal|es)/(?P<category>rg/a-carta|rg/podcast|rg/destacados|tvg/a-carta|informativos|en-serie)/(?:[^/]+/)*(?P<slug>[A-Za-z0-9-]*)-(?P<id>[0-9]{4,})?'
    _TESTS = [{
        'url': 'http://www.crtvg.es/tvg/a-carta/pepe-o-ingles-28-best-of',
        'info_dict': {
            'id': '594037',
            'ext': 'mp4',
            'title': 'The Best of... (O mellor de Pepe o Inglés)',
            'description': 'Lola conta como andan as cousas en Cruceiro un ano despois, con Pepe e Pilar por Londres e Filipa e o alcalde vivindo en Marbella e presenta o último episodio, un resume co mellor da serie, unha especie de propina como dia ela.',
            'series': 'Pepe o inglés',
            'release_date': '20130527',
        },
    }, {
        'url': 'http://www.crtvg.es/rg/podcast/a-bola-extra-a-bola-extra-do-dia-21-04-2020-4383702',
        'info_dict': {
            'id': '4383702',
            'ext': 'mp3',
            'title': 'A bóla extra do día 21/04/2020',
            'description': None,
            'series': 'A bóla extra',
            'release_date': '20200421',
        },
    }]

    def _real_extract(self, url):

        media_id = self._match_id(url)

        category = re.match(self._VALID_URL, url).group('category')
        webpage = self._download_webpage(url, media_id)

        if media_id is None or media_id == 'None':
            media_id = self._html_search_regex(
                r'metadata\[\'ns_st_ci\'\][ ]*=[ ]*(\d{4,})',
                webpage, 'media_id', group=1, fatal=False)

        # Radio Galega in mp3, otherwise mp4
        ext = 'mp3' if 'rg' in category else 'mp4'

        media_url = self._html_search_regex(
            r'https?://(?:www\.)?.*flumotion.com/videos/(?:[^/]+/)*?([A-Za-z0-9\-_]*)\.' + ext,
            webpage, 'media_url', group=0)

        if 'a-carta' in category or 'destacados' in category:
            title = unescapeHTML(self._html_search_regex(
                r'<h2 class="destacado-info-titulo-programa">(?:\s*)?([^\n\r]*)(?:\s*)?</h2>',
                webpage, 'title', group=1, fatal=False))
            description = unescapeHTML(self._html_search_regex(
                r'<div class="entrada-contenido">(?:\s*)?([^\n\r]*)(?:\s*)?',
                webpage, 'description', fatal=False))
            series = unescapeHTML(self._html_search_regex(
                r'<h2 class="decorativo">(?:\s*)?<a href="(?:[^"]*)?"(?:\s*)?title="([^"]*)?">',
                webpage, 'series', group=1, fatal=False))
            release_date = unescapeHTML(self._html_search_regex(
                r'<div class="entrada-blog-fecha">(?:\s*)?(?:\D*)?(\d{2}/\d{2}/\d{4})',
                webpage, 'release_date', group=1, fatal=False))
            release_date = unified_strdate(release_date)

        elif category == 'en-serie':
            title = unescapeHTML(self._html_search_regex(
                r'<div class="ficha">(?:\s*)?<h2>(.*)?</h2>',
                webpage, 'title', group=1, fatal=False))
            description = unescapeHTML(self._html_search_regex(
                r'<div class="ficha">(?:\s*)?<h2>(?:.*)?</h2>(?:\s*)<p>(.*)?</p>',
                webpage, 'description', fatal=False))
            series = unescapeHTML(self._html_search_regex(
                r'<div class="titulo-serie">(?:\s*)?<h1>(.*)?</h1>(?:\s*)',
                webpage, 'series', group=1, flags=re.S, fatal=False))
            release_date = unescapeHTML(self._html_search_regex(
                r'metadata\[\'ns_st_ddt\'\][ ]*=[ ]*\'?(\d{4}\-\d{2}\-\d{2})',
                webpage, 'release_date', group=1, fatal=False))
            release_date = unified_strdate(release_date)

        elif category == 'informativos':
            title = unescapeHTML(self._html_search_regex(
                r'<h3 class="entrada-titulo">(.*)?</h3>',
                webpage, 'title', group=1, fatal=False))
            description = unescapeHTML(self._html_search_meta(
                ('og:description', 'og:description'),
                webpage, 'description', fatal=False))
            series = 'Noticias de Galicia'
            release_date = unescapeHTML(self._html_search_regex(
                r'<div class="entrada-blog-fecha">(?:\s*)?(?:\D*)?(\d{2}/\d{2}/\d{4})',
                webpage, 'release_date', group=1, fatal=False))
            release_date = unified_strdate(release_date)

        elif category == 'rg/podcast':
            title = unescapeHTML(self._html_search_regex(
                r'<title>(.*)?</title>',
                webpage, 'series', group=1, fatal=False))
            description = None
            series = unescapeHTML(self._html_search_regex(
                r'<div class="titulo">(?:\s*)?<a href="(?:[^"]*)?"(?:\s*)?title="([^"]*)?">',
                webpage, 'series', group=1, fatal=False))
            release_date = unescapeHTML(self._html_search_regex(
                r'<title>(?:\D*)?(\d{2}/\d{2}/\d{4})',
                webpage, 'release_date', group=1, fatal=False))
            release_date = unified_strdate(release_date)

        else:
            title = unescapeHTML(self._html_search_meta(
                ('title', 'og:title'),
                webpage, 'title', fatal=False))
            if 'rg' not in category:
                description = unescapeHTML(self._html_search_meta(
                    ('og:description', 'og:description'),
                    webpage, 'description', fatal=False))
            else:
                description = None
            series = unescapeHTML(self._html_search_regex(
                r'<title>(.*)?</title>',
                webpage, 'series', group=1, fatal=False))
            release_date = None

        if title is not None and "|" in title:
            title = title.split("|")[0].rstrip()

        if series is not None and "|" in series:
            series = series.split("|")[0].rstrip()

        formats = []
        if 'rg' in category:
            formats.append({
                'format_id': 'audio',
                'url': media_url,
                'ext': ext,
                'vcode': None,
                'acodec': ext,
            })
        else:
            formats = self._extract_m3u8_formats(
                media_url + '/playlist.m3u8',
                media_id, ext='mp4', fatal=False)
        self._sort_formats(formats)

        return {'id': media_id,
                'title': title,
                'description': description,
                'series': series,
                'release_date': release_date,
                'formats': formats,
                }
