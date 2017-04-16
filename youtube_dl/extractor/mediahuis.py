# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .kaltura import KalturaIE
from ..utils import (
    smuggle_url
)


class MediahuisIE(InfoExtractor):
    """ Extractor for Mediahuis news sites """
    _VALID_URL = r'https?://(?:(?:www\.)?nieuwsblad\.be|(?:www\.)?gva\.be|(?:www\.)?standaard\.be|(?:www\.)?hbvl\.be)/.+?/dmf([0-9]+?)_(?P<id>[0-9]+)'
    IE_DESC = 'Het Nieuwsblad, de Standaard, Gazet van Antwerpen and Het Belang van Limburg'
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
        # Source: Kaltura
        {
            'url': 'http://www.nieuwsblad.be/cnt/dmf20151225_02037264',
            'md5': 'd4decdc7f105c26767b928c54c7d5184',
            'info_dict': {
                'id': '02037264',
                'ext': 'mov',
                'title': 'Exclusieve sportwagen brandt uit op weg naar winterberging',
                'description': 'Een exclusieve TVR Tuscon S is kerstdag op de Burkel helemaal uitgebrand. '
                               'De eigenaar van deze Britse sportauto was rond 11 uur onderweg om het voertuig na...',
                'thumbnail': 're:http.*jpg$',
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
        # Gazet van Antwerpen
        {
            'url': 'http://www.gva.be/cnt/dmf20170412_02832220/blind-meisje-met-autisme-reageert-op-hartverwarmende-wijze-wanneer-ze-straatmuzikant-hoort-spelen',
            'md5': '54fc7fb24dd187adb25ccd698c45ddef',
            'info_dict': {
                'id': '02832220',
                'ext': 'mp4',
                'title': 'Blind meisje met autisme reageert op hartverwarmende wijze wanneer ze straatmuzikant hoort spelen',
                'description': 'De zevenjarige Lacie is blind en lijdt aan autisme, maar haar liefde voor muziek is ze '
                               'duidelijk niet verloren. Toen het meisje afgelopen vrijdag samen met...',
                'thumbnail': 're:http.*jpg$',
                'upload_date': '20170412',
                'uploader_id': 'videoredactie@mediahuis.be',
                'timestamp': 1492014190,

            }
        },
        # Het Belang van Limburg
        {
            'url': 'http://www.hbvl.be/cnt/dmf20170413_02832693/video-bestuurder-krijgt-appelflauwte-en-rijdt-recht-woonkamer-binnen',
            'md5': '308f2683c3e22051c9751580607ace3d',
            'info_dict': {
                'id': '02832693',
                'ext': 'mov',
                'title': 'VIDEO. Bestuurder krijgt appelflauwte en rijdt recht woonkamer binnen',
                'description': 'Een BMW is donderdagmiddag in de living van een woning beland langs de Oudenaardse'
                               'steenweg in het Oost-Vlaamse Erpe-Mere. De BMW kwam van de oprit E40 gere...',
                'thumbnail': 're:http.*jpg$',
                'upload_date': '20170413',
                'uploader_id': 'video',
                'timestamp': 1492092669,
            }
        },
        # De Standaard (Kaltura, Dynamic Embed)
        {
            'url': 'http://www.standaard.be/cnt/dmf20170412_02831280',
            'md5': '490f0874ad308a6010292edd1a041b14',
            'info_dict': {
                'id': '02831280',
                'ext': 'mp4',
                'title': 'Zo klinkt een gitaar gemaakt van papier',
                'description': 'Gitaarbouwer Walter Verreydt bouwde een gitaar uit krantenpapier. Kan een papieren '
                               'gitaar zo goed klinken als een gitaar van tropisch hout? Blijkbaar wel. ...',
                'thumbnail': 're:http.*jpg$',
                'upload_date': '20170412',
                'uploader_id': 'videoredactie@mediahuis.be',
                'timestamp': 1492009206,
            }
        },
        # De Standaard (Kaltura, Auto Embed)
        {
            'url': 'http://www.standaard.be/cnt/dmf20170413_02832378',
            'md5': 'c3be760e20a9b49b3eac2536bc045b5b',
            'info_dict': {
                'id': '02832378',
                'ext': 'mp4',
                'title': 'VIDEO. Is bio ons geld waard?',
                'description': 'Is biologisch eten beter voor de wereld, of een sprookje voor naïeve consumenten? '
                               'Correspondente en voedingsjournaliste Dorien Knockaert neemt de kritiek v...',
                'thumbnail': 're:http.*jpg$',
                'upload_date': '20170412',
                'uploader_id': 'batchUser',
                'timestamp': 1491990547,
            }
        }
    ]

    def _real_extract(self, url):
        """ Extract the video info from the given mediahuis URL """
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        thumbnail = self._og_search_thumbnail(webpage)
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        url_type = None

        iframe_m = re.search(r'<script[^>]+src="(.+?kaltura.com.*?)"', webpage)
        if iframe_m:
            video_url = smuggle_url(KalturaIE._extract_url(webpage), {'source_url': url})
            url_type = 'url_transparent'

        iframe_m = re.search(r'<iframe[^>]+src="(.+?vier.be.*?)"', webpage)
        if iframe_m:
            video_url = (iframe_m.group(1))
            url_type = 'url_transparent'

        iframe_m = re.search(r'<iframe[^>]+src="(.+?vrt.be.*?)"', webpage)
        if iframe_m:
            webpage = self._download_webpage(iframe_m.group(1), "vrt-iframe")
            video_url = self._search_regex(r'sources.pdl = "(.*?)";', webpage, 'vrt-video')

        iframe_m = re.search(r'<iframe[^>]+src="(.+?vmma.be.*?)"', webpage)
        if iframe_m:
            webpage = self._download_webpage(iframe_m.group(1), "vmma-iframe")
            video_url = self._search_regex(r'<source src="(.*?)"', webpage, 'vmma-video')

        info = {
            'url': video_url,
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail
        }

        if url_type:
            info['_type'] = url_type

        return info
