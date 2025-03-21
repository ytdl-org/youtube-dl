# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    clean_html,
    parse_iso8601
)


class MujRozhlasIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mujrozhlas\.cz/(?P<id>[a-zA-Z0-9/-]+)'
    _TESTS = [{
        'url': 'https://www.mujrozhlas.cz/meteor/meteor-o-nejvetsim-matematikovi-nekonecnem-vesmiru-skakajicim-pavoukovi-hrani-surikat',
        'info_dict': {
            'id': 'meteor/meteor-o-nejvetsim-matematikovi-nekonecnem-vesmiru-skakajicim-pavoukovi-hrani-surikat',
            'ext': 'mp3',
            'title': 'Meteor o největším matematikovi, nekonečném vesmíru, skákajícím pavoukovi a hraní surikat',
            'description': 'Poslechněte si:01:00 Vymírající pták roku07:57 Největší experimentátor všech dob14:06 Největší matematik 20. století27:40 Jak si představit nekonečný vesmír?35:12 Pavouk, který skáče bunjee jumping41:34 Jak si hrají surikaty?Hovoří ornitolog Zdeněk Vermouzek, matematik Václav Chvátal nebo astronom Norbert Werner. Rubriku Stalo se tento den připravil ing. František Houdek.\xa0Z knihy\xa0Pozoruhodné objevy ze světa zvířat čte Zuzana Slavíková.\nPetr Sobotka',
            'timestamp': 1647272701,
            'upload_date': '20220314',
        }
    }, {
        'url': 'https://www.mujrozhlas.cz/podcast-vinohradska-12/its-humanitarian-disaster-mariupol-we-want-help-says-msfs-alex-wade',
        'info_dict': {
            'id': 'podcast-vinohradska-12/its-humanitarian-disaster-mariupol-we-want-help-says-msfs-alex-wade',
            'ext': 'mp3',
            'title': 'It\'s a humanitarian disaster in Mariupol. We want to help, says MSF‘s Alex Wade',
            'description': 'It is a humanitarian catastrophe. People in the southeast of Ukraine are dying in the streets and their neighbors have to bury them in the gardens. Those who are still alive, dont have food, water or medicine. I spoke to Alex Wade, an emergency coordinator for Doctors without Borders, who is in Dnipro. He is doing his best to help Ukrainians who are fleeing the war or staying to fight back.\nMatěj Skalický\n\nEdited by: Kateřina Pospíšilová\nSound design: Tomáš Černý\nResearched by:\xa0Alžběta Jurčová\nMusic:\xa0Martin Hůla',
            'timestamp': 1647442501,
            'upload_date': '20220316',
        }
    }]

    def _real_extract(self, url):
        audio_id = self._match_id(url)

        webpage = self._download_webpage(url, audio_id)

        content_id = self._html_search_regex(r'"contentId":"(.+?)"', webpage, 'content_id')
        content_url = 'https://api.mujrozhlas.cz/episodes/' + content_id

        content = self._download_json(content_url, content_id)
        attrs = content['data']['attributes']
        title = attrs['title']
        audio_url = content['data']['attributes']['audioLinks'][0]['url']
        audio_info = content['data']['attributes']['audioLinks'][0]
        duration = audio_info.get('duration')
        description = clean_html(attrs.get('description'))
        thumbnail = self._og_search_thumbnail(webpage)
        timestamp = parse_iso8601(self._og_search_property('updated_time', webpage, fatal=False))

        return {
            'id': audio_id,
            'url': audio_url,
            'title': title,
            'description': description,
            'duration': int_or_none(duration),
            'vcodec': 'none',
            'thumbnail': thumbnail,
            'timestamp': timestamp,
        }
