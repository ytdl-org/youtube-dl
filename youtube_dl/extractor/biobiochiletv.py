# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import remove_end


class BioBioChileTVIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.biobiochile\.cl/notas/(?:[^/]+/)+(?P<id>[^/]+)\.shtml'

    _TESTS = [{
        'url': 'http://tv.biobiochile.cl/notas/2015/10/21/sobre-camaras-y-camarillas-parlamentarias.shtml',
        'md5': '26f51f03cf580265defefb4518faec09',
        'info_dict': {
            'id': 'sobre-camaras-y-camarillas-parlamentarias',
            'ext': 'mp4',
            'title': 'Sobre Cámaras y camarillas parlamentarias',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'Fernando Atria',
        },
    }, {
        # different uploader layout
        'url': 'http://tv.biobiochile.cl/notas/2016/03/18/natalia-valdebenito-repasa-a-diputado-hasbun-paso-a-la-categoria-de-hablar-brutalidades.shtml',
        'md5': 'edc2e6b58974c46d5b047dea3c539ff3',
        'info_dict': {
            'id': 'natalia-valdebenito-repasa-a-diputado-hasbun-paso-a-la-categoria-de-hablar-brutalidades',
            'ext': 'mp4',
            'title': 'Natalia Valdebenito repasa a diputado Hasbún: Pasó a la categoría de hablar brutalidades',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'Piangella Obrador',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://tv.biobiochile.cl/notas/2015/10/22/ninos-transexuales-de-quien-es-la-decision.shtml',
        'only_matching': True,
    }, {
        'url': 'http://tv.biobiochile.cl/notas/2015/10/21/exclusivo-hector-pinto-formador-de-chupete-revela-version-del-ex-delantero-albo.shtml',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = remove_end(self._og_search_title(webpage), ' - BioBioChile TV')

        file_url = self._search_regex(
            r'loadFWPlayerVideo\([^,]+,\s*(["\'])(?P<url>.+?)\1',
            webpage, 'file url', group='url')

        base_url = self._search_regex(
            r'file\s*:\s*(["\'])(?P<url>.+?)\1\s*\+\s*fileURL', webpage,
            'base url', default='http://unlimited2-cl.digitalproserver.com/bbtv/',
            group='url')

        formats = self._extract_m3u8_formats(
            '%s%s/playlist.m3u8' % (base_url, file_url), video_id, 'mp4',
            entry_protocol='m3u8_native', m3u8_id='hls', fatal=False)
        f = {
            'url': '%s%s' % (base_url, file_url),
            'format_id': 'http',
            'protocol': 'http',
            'preference': 1,
        }
        if formats:
            f_copy = formats[-1].copy()
            f_copy.update(f)
            f = f_copy
        formats.append(f)
        self._sort_formats(formats)

        thumbnail = self._og_search_thumbnail(webpage)
        uploader = self._html_search_regex(
            r'<a[^>]+href=["\']https?://busca\.biobiochile\.cl/author[^>]+>(.+?)</a>',
            webpage, 'uploader', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'formats': formats,
        }
