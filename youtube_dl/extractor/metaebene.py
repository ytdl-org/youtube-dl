# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class MetaebeneIE(InfoExtractor):
    _VALID_URL = r'''(?x)^(?:https?://)?
                    (?:cre\.fm/
                    |logbuch-netzpolitik\.de/
                    |forschergeist\.de/podcast/
                    |freakshow\.fm/podcast/
                    |raumzeit-podcast.de/([^/]+/){3}
                    |fokus-europa.de/podcast/)
                    (?P<id>[^-]+)[^\s]*'''
    _TESTS = [{
        'url': 'https://cre.fm/cre217-mythos-68er',
        'info_dict': {
            'id': 'cre217',
            'ext': 'opus',
            'formats': 'mincount:4',
            'title': 'CRE217 Mythos 68er',
            'description': 'md5:6692fbff3b6f5b2df6fdc307a5271492',
            'site_name': 'CRE: Technik, Kultur, Gesellschaft',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://logbuch-netzpolitik.de/lnp247-lastesel-mit-glasfaseranschluss',
        'info_dict': {
            'id': 'lnp247',
            'ext': 'oga',
            'formats': 'mincount:4',
            'title': 'LNP247 Lastesel mit Glasfaseranschluss',
            'description': 'md5:9319166b6cfb8054f2875790a77cae09',
            'site_name': 'Logbuch:Netzpolitik',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://forschergeist.de/podcast/fg054-urbane-resilienz',
        'info_dict': {
            'id': 'fg054',
            'ext': 'opus',
            'formats': 'mincount:4',
            'title': 'FG054 Urbane Resilienz',
            'description': 'md5:2e76c5f8ee5f44b49869398e78cd1e50',
            'site_name': 'Forschergeist',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://raumzeit-podcast.de/2018/03/14/rz071-asteroidenabwehr/',
        'info_dict': {
            'id': 'rz071',
            'ext': 'opus',
            'formats': 'mincount:4',
            'title': 'RZ071 Asteroidenabwehr',
            'description': 'md5:bcdac8c0dc66a3d8ca14610009df87e1',
            'site_name': 'Raumzeit',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://fokus-europa.de/podcast/fe025-rechtspopulismus-in-europa/',
        'info_dict': {
            'id': 'fe025',
            'ext': 'opus',
            'formats': 'mincount:4',
            'title': 'FE025 Rechtspopulismus in Europa',
            'description': 'md5:f53fb44567aea7ff43daf9b45106c6e6',
            'site_name': 'Fokus Europa',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):

        content_id = self._match_id(url).strip('/')
        webpage = self._download_webpage(url, content_id)

        audio_reg = self._og_regexes('audio')
        audio_type_reg = self._og_regexes('audio:type')

        formats = []
        for audio_url, audio_type in zip(
                re.findall(audio_reg[0], webpage),
                re.findall(audio_type_reg[0], webpage)):
            formats.append({
                'url': audio_url[0],
                'format_id': audio_type[0]})

        return {
            'id': content_id,
            'title': self._og_search_title(webpage),
            'site_name': self._og_search_property('site_name', webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
        }
