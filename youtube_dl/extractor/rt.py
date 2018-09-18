# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .ora import OraTVIE
from .youtube import YoutubeIE
from .generic import GenericIE


class RTIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rt\.com/.+/(?P<id>\d+)-.+'
    _TESTS = [
        {
            'url': 'https://www.rt.com/shows/alex-salmond-show/438343-britain-railway-london-communities/',
            'md5': '0d8f6f86673ee8d72215c8d060170a5e',
            'info_dict': {
                'id': '438343',
                'ext': 'mp4',
                'title': 'HS2: The human cost… RT — The Alex Salmond Show'
            },
            'params': {
                'skip_download': False,
            }
        },
        {
            'url': 'https://www.rt.com/shows/larry-king-now/438502-andie-macdowell-on-ageism-in/',
            'md5': '5852a10576b4add6b250f864546033f4',
            'info_dict': {
                'id': '57786',
                'ext': 'mp4',
                'title': 'md5:fa0da906fbfc7974da14ca53424b1a3a',
                'description': 'md5:07b6bce4ad4043b136e21ef9539d46c5'
            },
            'params': {
                'skip_download': False,
            }
        },
        {
            'url': 'https://www.rt.com/shows/icymi-with-polly-boiko/438450-musk-smoke-marijuana-radio/',
            'md5': '2c2fe0f78f1ca225e82fb7b27c8fd3f5',
            'info_dict': {
                'id': 'SHxygmDAkNE',
                'ext': 'mp4',
                'title': 'md5:004bcbc650d8294c5cdefcc470c3cd3d',
                'description': 'md5:99e8c3456f6904383399aeeb10784c8b',
                'upload_date': '20180914',
                'uploader_id': 'UCdgFmrDeP9nWj_eDKW6j9kQ',
                'uploader': 'ICYMI'
            },
            'params': {
                'skip_download': False,
            }
        },
        {
            'url': 'https://www.rt.com/news/438686-syria-russia-s200-il20/',
            'md5': '03acfb2a27a13fb74eb5c192e53bf7e0',
            'info_dict': {
                'id': 'YEioP7zJzMc',
                'ext': 'mp4',
                'title': 'md5:e703b7c8d88725c1530661d61a626303',
                'description': 'md5:8ab844abcd296d15f4a99b089e1e1347',
                'upload_date': '20180918',
                'uploader_id': 'RussiaToday',
                'uploader': 'RT'
            },
            'params': {
                'skip_download': False,
            }
        }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_title = self._html_search_regex(
            r'<title>(.+?)</title>', webpage, 'title', fatal=False) or self._html_search_meta(['og:title', 'twitter:title'], webpage)

        oratv = self._search_regex(
            r'src=["\']((https?:)?//(?:www\.)ora\.tv[^\'"]+)', webpage, 'oratv', fatal=False, default=None)

        # some videos are embedded from ORATV
        if oratv is not None:

            oratv_embedded_webpage = self._download_webpage(oratv, video_id)
            ora_website_url = self._search_regex(
                r'<link[^>]rel=["\']canonical["\'].+href=["\']([^\'"]+)', oratv_embedded_webpage, 'orawebsite')

            return self.url_result(ora_website_url, ie=OraTVIE.ie_key())

        # some videos are embedded from youtube
        yturl = self._search_regex(
            r'<div[^>]+\bdata-url=["\']((https?:)?//(?:www\.)youtube\.[^\'"]+)', webpage, 'youtube', fatal=False, default=None) or self._search_regex(
            r'<iframe[^>]+\bsrc=["\']((https?:)?//(?:www\.)youtube\.[^\'"]+)', webpage, 'youtube', fatal=False, default=None)

        if yturl is not None:
            return self.url_result(yturl, ie=YoutubeIE.ie_key())

        # default RT's CDN
        video_url = self._search_regex(
            r'file:\s*["\'](https?://[^\'"]+)', webpage, 'url', fatal=False, default=None)

        if video_url is not None:

            return {
                'id': video_id,
                'title': video_title,
                'url': video_url
            }

        # attempt to use generic
        return self.url_result(url, ie=GenericIE.ie_key())
