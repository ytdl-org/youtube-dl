# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    clean_html,
)


class MujRozhlasIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mujrozhlas\.cz/(?P<id>[a-zA-Z0-9/-]+)'
    _TESTS = [{
        'url': 'https://www.mujrozhlas.cz/meteor/meteor-o-nejvetsim-matematikovi-nekonecnem-vesmiru-skakajicim-pavoukovi-hrani-surikat',
        'info_dict': {
            'id': 'meteor/meteor-o-nejvetsim-matematikovi-nekonecnem-vesmiru-skakajicim-pavoukovi-hrani-surikat',
            'ext': 'mp3',
            'title': 'Meteor o největším matematikovi, nekonečném vesmíru, skákajícím pavoukovi a hraní surikat',
            'description': 'Poslechněte si:01:00 Vymírající pták roku07:57 Největší experimentátor všech dob14:06 Největší matematik 20. století27:40 Jak si představit nekonečný vesmír?35:12 Pavouk, který skáče bunjee jumping41:34 Jak si hrají surikaty?Hovoří ornitolog Zdeněk Vermouzek, matematik Václav Chvátal nebo astronom Norbert Werner. Rubriku Stalo se tento den připravil ing. František Houdek.\xa0Z knihy\xa0Pozoruhodné objevy ze světa zvířat čte Zuzana Slavíková.\nPetr Sobotka'
        }
    }, {
        'url': 'https://www.mujrozhlas.cz/podcast-vinohradska-12/its-humanitarian-disaster-mariupol-we-want-help-says-msfs-alex-wade',
        'info_dict': {
            'id': 'podcast-vinohradska-12/its-humanitarian-disaster-mariupol-we-want-help-says-msfs-alex-wade',
            'ext': 'mp3',
            'title': 'Meteor o největším matematikovi, nekonečném vesmíru, skákajícím pavoukovi a hraní surikat',
            'description': 'Poslechněte si:01:00 Vymírající pták roku07:57 Největší experimentátor všech dob14:06 Největší matematik 20. století27:40 Jak si představit nekonečný vesmír?35:12 Pavouk, který skáče bunjee jumping41:34 Jak si hrají surikaty?Hovoří ornitolog Zdeněk Vermouzek, matematik Václav Chvátal nebo astronom Norbert Werner. Rubriku Stalo se tento den připravil ing. František Houdek.\xa0Z knihy\xa0Pozoruhodné objevy ze světa zvířat čte Zuzana Slavíková.\nPetr Sobotka'
        }
    }]

    def _real_extract(self, url):
        audio_id = self._match_id(url)

        webpage = self._download_webpage(url, audio_id)

        content_id = self._html_search_regex(r'\"contentId\":\"(.+?)\"', webpage, 'content_id')
        content_url = 'https://api.mujrozhlas.cz/episodes/' + content_id

        content = self._download_json(content_url, content_id)
        attrs = content['data']['attributes']
        title = attrs['title']
        audio_info = content['data']['attributes']['audioLinks'][0]
        duration = audio_info.get('duration')
        description = clean_html(attrs.get('description'))
        audio_url = audio_info.get('url')

        return {
            'id': audio_id,
            'url': audio_url,
            'title': title,
            'description': description,
            'duration': int_or_none(duration),
            'vcodec': 'none',
        }
