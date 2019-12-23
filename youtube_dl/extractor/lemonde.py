# coding: utf-8

from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError
import re


class LemondeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?lemonde\.fr/(?:[^/]+/)*(?P<id>[^/]+)\.html'
    _TESTS = [{
        # Youtube embeded
        'url': 'http://www.lemonde.fr/police-justice/video/2016/01/19/comprendre-l-affaire-bygmalion-en-cinq-minutes_4849702_1653578.html',
        'md5': 'bf4645c22f7bde53a2a55cd2b089ee57',
        'info_dict': {
            'id': 'tiv9ZFUrFj4',
            'ext': 'mp4',
            'title': "L’affaire Bygmalion expliquée en\xa05\xa0minutes",
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 296,
            'upload_date': '20181025',
            'uploader': 'Le Monde',
            'uploader_id': 'LeMonde',
            'description': 'Dans l’affaire Bygmalion, la justice a confirmé le renvoi en correctionnelle de Nicolas Sarkozy, jeudi 25 octobre. Dans la foulée, son avocat Thierry Herzog a annoncé que l’ancien président de la République allait former un pourvoi en cassation.\n\nLe 5 mars 2014, le parquet de Paris ouvrait une enquête préliminaire pour « faux », «abus de biens sociaux » et « abus de confiance » visant la société Bygmalion, soupçonnée d’être au centre d’un système de fausses factures. Grâce à elles, les responsables de Bygmalion et de sa filiale Event and Cie, ainsi que des membres de l’UMP — devenue Les Républicains en 2015 — et de l’équipe de campagne de Nicolas Sarkozy, auraient fait en sorte que les dépenses de campagne du candidat pour l’élection présidentielle de 2012 restent inférieures au plafond autorisé par la loi.\n\nQuatorze personnes, dont Guillaume Lambert, qui était le directeur de campagne de Nicolas Sarkozy, et Jérôme Lavrilleux, alors directeur adjoint de campagne, sont renvoyées en procès. Jean-François Copé, lui, a bénéficié d’un non-lieu et est définitivement blanchi.\n\nComment fonctionnait ce système de fausses factures ? Explications avec cette vidéo réalisée en janvier 2016.\n_______\n\nAbonnez-vous à la chaîne YouTube du Monde dès maintenant :\nhttp://www.youtube.com/subscription_center?add_user=LeMonde\n_______\n\nAbonnez-vous à la chaîne YouTube du Monde dès maintenant :\nhttp://www.youtube.com/subscription_center?add_user=LeMonde',
        },
    }, {
        # Dailymotion embeded
        'url': 'http://www.lemonde.fr/les-decodeurs/article/2016/10/18/tout-comprendre-du-ceta-le-petit-cousin-du-traite-transatlantique_5015920_4355770.html',
        'info_dict': {
            'id': 'x4yejm2',
            'ext': 'mp4',
            'title': "CETA : quelles suites l'accord commercial entre l'Europe et le Canada ?",
            'duration': 326,
            'upload_date': '20161021',
            'timestamp': 1477044897,
            'uploader_id': 'x1wd0c',
            'uploader': 'Le Monde.fr',
            'description': 'CETA. 4 lettres pour Comprehensive Economic and Trade Agreement, ou Accord économique et commercial global). Un nom un peu barbare pour un traité transatlantique, cousin du Tafta, qui agite en ce moment l’actualité européenne.\xa0Pour comprendre les enjeux de cet accord commercial, notre spécialiste Maxime Vaudano.'
        }
    }]

    _PROVIDERS = {
        "youtube": "https://www.youtube.com/embed/{}",
        "dailymotion": "https://www.dailymotion.com/video/{}"
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        mobj = re.search(r'data-id="(?P<id>.+)" data-provider="(?P<provider>[^ ]+)"', webpage)
        video_id = mobj.group('id')
        provider = mobj.group('provider')

        if(provider not in self._PROVIDERS):
            raise ExtractorError('Unsupported provider ' % provider)

        embeded_url = self._PROVIDERS.get(provider, "").format(video_id)

        return {
            '_type': 'url',
            'url': embeded_url
        }
