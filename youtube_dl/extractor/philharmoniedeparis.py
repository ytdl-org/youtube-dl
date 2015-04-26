# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    parse_iso8601,
    unified_strdate,
)

class PhilharmonieDeParisIE(InfoExtractor):
    _VALID_URL = r'http://live\.philharmoniedeparis\.fr/concert/(?P<id>\d+)(?:/|\.html)'
    _TESTS = [{
        'url': 'http://live.philharmoniedeparis.fr/concert/1032066.html',
        'info_dict': {
            'id': '1032066',
            'ext': 'mp4',
            'title': "Week-end Bach. Passion selon saint Jean. Akademie für alte Musik Berlin, Rias Kammerchor, René Jacobs",
            'upload_date': '20150404',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        fichier_nom = self._html_search_regex(r'\sflashvars\s*:\s*\{\s*fichier_nom\s*:\s*\'(.*?)\'\s*,', webpage, 'fichier_nom')

        playlist = self._download_xml('http://live.philharmoniedeparis.fr' + fichier_nom, video_id)

        concert = playlist.find('.//concert')

        formats = []
        info_dict = {
            'id': video_id,
            'title': concert.find('./titre').text,
            'formats': formats,
        }

        if concert.attrib.get('heure'):
            info_dict['timestamp'] = parse_iso8601(('%s-%s-%s%s') % (
                concert.attrib['date'][0:4],
                concert.attrib['date'][4:6],
                concert.attrib['date'][6:8],
                concert.attrib['heure']
            ))
        else:
            info_dict['upload_date'] = concert.attrib['date']

        fichiers = concert.find('./fichiers')
        for fichier in fichiers.findall('./fichier'):
            # Sometimes <ficher>s have no attributes at all. Skip them.
            if 'url' not in fichier.attrib:
                continue

            formats.append({
                'format_id': 'lq',
                'url': fichiers.attrib['serveurstream'],
                'ext': determine_ext(fichier.attrib['url']),
                'play_path': fichier.attrib['url'],
                'width': int_or_none(concert.attrib['largeur']),
                'height': int_or_none(concert.attrib['hauteur']),
                'quality': 1,
            })

            formats.append({
                'format_id': 'hq',
                'url': fichiers.attrib['serveurstream'],
                'ext': determine_ext(fichier.attrib['url_hd']),
                'play_path': fichier.attrib['url_hd'],
                'width': int_or_none(concert.attrib['largeur_hd']),
                'height': int_or_none(concert.attrib['hauteur_hd']),
                'quality': 2,
            })

        return info_dict
