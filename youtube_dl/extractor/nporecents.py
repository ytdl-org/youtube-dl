#!/usr/bin/python
from .common import InfoExtractor

import re
import xml.etree.ElementTree as ET


class NPORecentsIE(InfoExtractor):
    IE_Name = 'npo:recents'
    _VALID_URL = r'(?:https?://)?(?:www\.)?npo\.nl/(?P<alt_id>[^/]+)/(?P<program_id>\w+_\d+)'
    _TEST = {
        'url': 'https://www.npo.nl/keuringsdienst-van-waarde/KN_1678993',
        'info_dict': {
            'title': 'Keuringsdienst van Waarde',
            'id': 'KN_1678993',
            'description': 'In dit programma staat centraal wat fabrikanten ons als consumenten vertellen. Klopt het wat ze claimen en wat ze ons in reclames verkopen? Verslaggevers Teun van de Keuken, Sofie van den Enk, Daan Nieber, Ersin Kiris, Marijn Frank en Maarten Remmers nemen de telefoon ter hand en bellen er actief op los. Ze stellen simpele vragen en krijgen de meest verbazingwekkende antwoorden op food, non-food en nieuwsgerelateerde kwesties. Prikkelend, onderzoekend en vasthoudend. Keuringsdienst van Waarde: simpele vragen,verbazingwekkende antwoorden.'
        },
        'playlist_mincount': 8
    }

    def _extract_entries(self, webpage, program_id, program_url):
        is_npo3 = 'www-assets.npo.nl/uploads/tv_channel/265/logo/smaller_npo3-logo.png' in webpage

        if is_npo3:
            episodes_url = '{}//search?category=broadcasts&page=1'.format(
                program_url)
        else:
            episodes_url = '{}/search?media_type=broadcast&start=0&rows=8'.format(
                program_url)

        episodes = self._download_webpage(
            episodes_url, program_id, note='Retrieving episodes')
        tree = ET.fromstring(episodes.encode('utf-8'))
        for element in tree.findall('.//div'):
            if 'span4' in element.get('class'):
                hyperlink = element.find('.//a')
                inactive = hyperlink.find(
                    './div[@class="program-not-available"]')
                if inactive is None:
                    yield self.url_result(
                        url='http://npo.nl{}'.format(hyperlink.get('href')),
                        video_title=self._og_search_title(webpage))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        alt_id = mobj.group('alt_id')
        program_id = mobj.group('program_id')
        webpage = self._download_webpage(url, program_id)
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        entries = self._extract_entries(webpage, program_id, url)

        return {
            '_type': 'playlist',
            'id': program_id,
            'display_id': alt_id,
            'title': title,
            'description': description,
            'entries': entries
        }
