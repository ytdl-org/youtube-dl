# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    smuggle_url
)


class NieuwsbladIE(InfoExtractor):
    """ Extractor for www.nieuwsblad.be """
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
            'md5': 'd4decdc7f105c26767b928c54c7d5184',
            'info_dict': {
                'id': '1_z4jndqki',
                'ext': 'mov',
                'title': 'autobrand Peer',
                'thumbnail': 're:^https?://.*/thumbnail/.*',
                'timestamp': int,
                'upload_date': '20151225',
                'uploader_id': 'dcc-video-manager-hbvl@mediahuis.be'
            }
        },
    ]

    def _real_extract(self, url):
        """ Extract the video info from the given 'nieuwsblad' URL """
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
        """ Delegate the video extraction to 'Kaltura' extractor """
        kaltura_id = self._search_regex(r'entry_id\s*:\s*\"(.+?)\"', web_page, 'kaltura_id')
        kaltura_wid = self._search_regex(r'wid\s*\:\s*\"(.+?)\"', web_page, 'kaltura_wid')
        kaltura_uiconf_id = self._search_regex(r'uiconf_id\s*:\s*\"(.+?)\"', web_page, 'kaltura_uiconf_id')
        kaltura_url = (
            'https://cdnapisec.kaltura.com/index.php/kwidget/wid/{0}/uiconf_id/{1}/entry_id/{2}'
                .format(kaltura_wid, kaltura_uiconf_id, kaltura_id)
        )
        url_with_source = smuggle_url(kaltura_url, {'source_url': url})
        return self.url_result(url_with_source, 'Kaltura')
