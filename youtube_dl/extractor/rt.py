# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .ora import OraTVIE
from .youtube import YoutubeIE


class RTIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rt\.com/.*/(?P<id>\d+)-.*'
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
                'title': 'Andie MacDowell on ageism in Hollywood, fame, & forest protection',
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
                'title': u'ICYMI: Is Elon Musk Tony Stark, or just stark raving mad?',
                'description': 'md5:99e8c3456f6904383399aeeb10784c8b',
                'upload_date': '20180914',
                'uploader_id': 'UCdgFmrDeP9nWj_eDKW6j9kQ',
                'uploader': 'ICYMI'
            },
            'params': {
                'skip_download': False,
            }
        }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_title = self._search_regex(
            r'<title>(.+?)</title>', webpage, 'title')
        # default RT's CDN
        video_url = self._search_regex(
            r'file: "(https://cdnv.+?)",', webpage, 'url', fatal=False, default=None)

        if video_url is None:

            oratv = self._search_regex(
                r'src="(//www\.ora\.tv.+?)"', webpage, 'oratv', fatal=False, default=None)

            if oratv is not None:
                # some videos are embedded from ORATV

                oratv_embedded_webpage = self._download_webpage(oratv, video_id)
                ora_website_url = self._search_regex(
                    r'<link rel="canonical" href="(.+?)"', oratv_embedded_webpage, 'orawebsite')
                oratvie = OraTVIE()
                oratvie._downloader = self._downloader
                return oratvie._real_extract(ora_website_url)
            else:
                # some videos are embedded from youtube

                yturl = self._search_regex(
                    r'data-url="(//www\.youtube\.com/embed.+?)"', webpage, 'youtube', fatal=False, default=None)
                ytie = YoutubeIE()
                ytie._downloader = self._downloader
                return ytie._real_extract(yturl)

        return {
            'id': video_id,
            'title': video_title,
            'url': video_url
        }
