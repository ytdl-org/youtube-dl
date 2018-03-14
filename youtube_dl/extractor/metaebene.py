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
                    |fokus-europa.de/podcast/
                    |not-safe-for-work.de/
                    |kolophon.oreilly.de/
                    |der-lautsprecher.de/
                    |newz-of-the-world.com/
                    |diegesellschafter.metaebene.me/)
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
    }, {
        'url': 'https://not-safe-for-work.de/nsfw098-publikationspromiskuitaet/',
        'info_dict': {
            'id': 'nsfw098',
            'ext': 'opus',
            'formats': 'mincount:4',
            'title': 'NSFW098 Publikationspromiskuität',
            'description': 'md5:b4b503a38c1dc37950fd40b7969c28d5',
            'site_name': 'Not Safe For Work',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://kolophon.oreilly.de/kol017-startups/',
        'info_dict': {
            'id': 'kol017',
            'ext': 'opus',
            'formats': 'mincount:4',
            'title': 'KOL017 Startups',
            'description': 'md5:c2db87c7be046c9f3c712584912db999',
            'site_name': 'Kolophon',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://der-lautsprecher.de/ls018-audioformate-fuer-podcasts',
        'info_dict': {
            'id': 'ls018',
            'ext': 'opus',
            'formats': 'mincount:4',
            'title': 'LS018 Audioformate für Podcasts',
            'description': 'md5:9eea235a49b6ed8bf6b11fa112735e47',
            'site_name': 'Der Lautsprecher',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://newz-of-the-world.com/newz088-were-gonna-miss-him-when-hes-gone/',
        'info_dict': {
            'id': 'newz088',
            'ext': 'oga',
            'formats': 'mincount:4',
            'title': 'NEWZ088 We\'re gonna miss him when he\'s gone',
            'description': 'md5:f48c83fc3f10c950307dca5d318ae346',
            'site_name': 'Newz of the World',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://diegesellschafter.metaebene.me/dg024-freiwilliges-soziales-jahr/',
        'info_dict': {
            'id': 'dg024',
            'ext': 'oga',
            'formats': 'mincount:4',
            'title': 'DG024 Freiwilliges Soziales Jahr',
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

        # The "Die Gesellschafter" series is discontinued and the description can't be extracted easily.
        # This is a workaround to suppress the warning and thus make it testable and avoid bug reports.
        if re.match(r'https?://(?:www\.)?diegesellschafter.metaebene.me/(?P<id>[^-]+)[^\s]*', url):
            description = None
        else:
            description = self._og_search_description(webpage)

        return {
            'id': content_id,
            'title': self._og_search_title(webpage),
            'site_name': self._og_search_property('site_name', webpage),
            'description': description,
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
        }
