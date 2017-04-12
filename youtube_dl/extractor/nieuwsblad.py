# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .kaltura import KalturaIE
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
                'description': 'Er is misschien toch goed nieuws voor de zieke Pauline (3). Het Riziv buigt zich'
                               ' namelijk over de vraag om de peperdure behandeling van 15.000 euro terug t...',
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
                'description': 'De metro rijdt niet, de scholen en crèches zijn dicht, vele winkels zijn gesloten. '
                               'Fotograaf Jimmy Kets brengt Brussel vandaag in beeld. Maar hij toont ook...',
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
        # Source: Vier.be
        {
            'url': 'http://www.nieuwsblad.be/cnt/dmf20170411_02829396',
            'md5': '35cb487bfd8c61fe38c9838420fd0de6',
            'info_dict': {
                'id': '02829396',
                'ext': 'mp4',
                'title': 'Dit is het nieuwste speeltje van Michel Van den Brande',
                'description': 'In de jongste aflevering van \'The Sky is the Limit\' pronkt Michel Van den Brande'
                               ' met zijn nieuwste speeltje: een glanzende BMW. Een van zijn medewerkers ma...',
                'thumbnail': 're:^https?://.*\.png$',
            }
        },
    ]

    def _real_extract(self, url):
        """ Extract the video info from the given 'nieuwsblad' URL """
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        iframe_m = re.search(r'<script[^>]+src="(.+?kaltura.com.*?)"', webpage)
        if iframe_m:
            kaltura_url = KalturaIE._extract_url(webpage)
            url_with_source = smuggle_url(kaltura_url, {'source_url': url})
            return self.url_result(url_with_source, 'Kaltura')

        iframe_m = re.search(r'<iframe[^>]+src="(.+?vier.be.*?)"', webpage)
        if iframe_m:
            vier_url = iframe_m.group(1)
            url_with_source = smuggle_url(vier_url, {'source_url': url, 'video_id': video_id})
            return self.url_result(url_with_source, 'Vier')

        thumbnail = self._og_search_thumbnail(webpage)
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)

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
            'description': description,
            'thumbnail': thumbnail
        }
