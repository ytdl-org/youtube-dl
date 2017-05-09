# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class PhilharmonieTvIE(InfoExtractor):
    _VALID_URL = r'http://www\.philharmonie\.tv/veranstaltung/(?P<id>.*?)/'
    _TESTS = [
        {
            'url': 'http://www.philharmonie.tv/veranstaltung/26/',
            'md5': '4cebde1eb60a53782d4f3992cbd46ec8',
            'info_dict': {
                'id': '28',
                'ext': 'flv',
                'title': u'03.05.2016 Tuesday 20:00 Uhr Konzert vom 03.05. ACHT BR\xdcCKEN | Musik f\xfcr K\xf6ln.  Hauschka, G. Schwellenbach, D. Brandt, P. Frick, E. Sarp, J. Farah: Reich'
            }
        }
    ]
    IE_NAME = 'philharmonie.tv'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        source_url = self._search_regex(
            r'<iframe id="vidframe".*?data-src="(https://playout.3qsdn.com/[\w-]+)"',
            webpage,
            'source url')

        jscript_source = self._download_webpage(source_url + '?js=true', video_id)
        manifest_url = self._search_regex(
            r'src: "(https://sdn-global-http-cache\.3qsdn.com/vod/_definst_/.*?/manifest.f4m)",',
            jscript_source,
            'manifest url')

        formats = self._extract_f4m_formats(manifest_url, video_id, f4m_id='hds', fatal=False)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
        }
