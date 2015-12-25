# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    smuggle_url
)


class NieuwsbladIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nieuwsblad\.be/.+?/dmf([0-9]+?)_(?P<id>[0-9]+)'
    _TESTS = [
        # Source: VMMA
        {
            'url': 'http://www.nieuwsblad.be/cnt/dmf20151224_02036890',
            'md5': '3dcf2c3a140d8e54dd8376d4c4a609f4',
            'info_dict': {
                'id': '02036890',
                'ext': 'mp4',
                'title': 'Krijgt zieke Pauline (3) het mooiste kerstcadeau?',
                'thumbnail': 're:http.*jpg$',
            }
        },
        # Source: VRT
        {
            'url': 'http://www.nieuwsblad.be/cnt/dmf20151124_01986463',
            'md5': '8e46cb7ddfddeb64735fa39f105002c2',
            'info_dict': {
                'id': '01986463',
                'ext': 'mp4',
                'title': 'Angst voor terreur: fotograaf toont hoe hij de werkelijkheid kan manipuleren',
                'thumbnail': 're:http.*jpg$',
            }
        },
        # Source: Mediahuis (using kaltura)
        {
            'url': 'http://www.nieuwsblad.be/cnt/dmf20151225_02037264',
            'md5': 'a9580438899f6355550fe1d44d4cddb9',
            'info_dict': {
                'id': '1_z4jndqki',
                'ext': 'mp4',
                'title': 'autobrand Peer',
                'thumbnail': 're:^https?://.*/thumbnail/.*',
                'timestamp': int,
                'upload_date': '20151225',
                'uploader_id': 'dcc-video-manager-hbvl@mediahuis.be'
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        iframe_m = re.search(r'<script[^>]+src="(.+?kaltura.com.*?)"', webpage)
        if iframe_m:
            return self._extract_kaltura(url, webpage)

        thumbnail = self._og_search_thumbnail(webpage)
        title = self._og_search_title(webpage)

        iframe_m = re.search(r'<iframe[^>]+src="(.+?vrt.be.*?)"', webpage)
        if iframe_m:
            webpage = self._download_webpage(iframe_m.group(1), "vrt-iframe")
            video_url = self._search_regex(r'sources.pdl = "(.*?)";', webpage, 'vrt-video')

        iframe_m = re.search(r'<iframe[^>]+src="(.+?vmma.be.*?)"', webpage)
        if iframe_m:
            webpage = self._download_webpage(iframe_m.group(1), "vmma-iframe")
            video_url = self._search_regex(r'<source src="(.*?)"', webpage, 'vmma-video')

        return {
            'url': video_url,
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail
        }

    def _extract_kaltura(self, url, web_page):
        kaltura_id = self._search_regex(r'\'entry_id\': \'(.+?)\'', web_page, 'kaltura_id')
        kaltura_wid = self._search_regex(r'\'wid\': \'(.+?)\'', web_page, 'kaltura_wid')
        kaltura_uiconf_id = self._search_regex(r'\'uiconf_id\': \'(.+?)\'', web_page, 'kaltura_uiconf_id')
        kaltura_url = (
            'https://cdnapisec.kaltura.com/index.php/kwidget/wid/%s/uiconf_id/%s/entry_id/%s' %
            (kaltura_wid, kaltura_uiconf_id, kaltura_id)
        )
        url_with_source = smuggle_url(kaltura_url, {'source_url': url})
        return self.url_result(url_with_source, 'Kaltura')
