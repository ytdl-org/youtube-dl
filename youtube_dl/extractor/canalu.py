# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    month_by_name,
    unescapeHTML
)
from re import DOTALL


class CanalUIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?canal-u\.tv/video/(?P<id>.*)'
    _TESTS = [
        {
            'url': 'https://www.canal-u.tv/video/ecole_normale_superieure_de_lyon/gouvernement.3118',
            'md5': '9c185d26b232c3c06d805c0d639af254',
            'info_dict': {
                'id': 'ecole_normale_superieure_de_lyon/gouvernement.3118',
                'ext': 'mp4',
                'duration': 600,
                'creator': 'SENELLART Michel',
                'title': 'Gouvernement',
                'description': 'Les essentiels : La philo par les mots - Gouvernement',
                'thumbnail': 'https://www.canal-u.tv/media/images/groupe_ens_lsh/gouvernement_3118/vignette.les.essentiels.jpg',
                'release_date': '20071015'}
        },
        {
            'url': 'https://www.canal-u.tv/video/ecole_normale_superieure_de_lyon/les_competences_en_situation_d_apprentissage.20850',
            'md5': 'f06aab78bf60c2a2340a733c18a5ef10',
            'info_dict': {
                'id': 'ecole_normale_superieure_de_lyon/les_competences_en_situation_d_apprentissage.20850',
                'ext': 'mp4',
                'duration': 360,
                'creator': 'COULET Jean-Claude',
                'title': 'Les compétences en situation d\'apprentissage',
                'description': 'Cette capsule présente comment on peut décliner la notion de compétence,\r  dans les situations pédagogiques, en donnant un sens précis aux \r concepts de situation, tâche, et activité. Elle ouvre des pistes de \r réflexion sur l\'articulation de ces notions dans les situations \r d\'éducation et de formation.',
                'thumbnail': 'https://www.canal-u.tv/media/images/groupe_ens_lsh/les.comp.tences.en.situation.d.apprentissage_20850/craies.jpg',
                'release_date': '20151215',
            }
        }]

    def _real_extract(self, url):
        video = {}
        video_id = self._match_id(url)
        video['id'] = video_id
        webpage = self._download_webpage(url, video_id)

        video['title'] = self._og_search_title(webpage)
        video['url'] = self._html_search_regex(r'file: "(.*?\.mp4)",', webpage, 'url')
        video['ext'] = 'mp4'

        video['thumbnail'] = self._og_search_thumbnail(webpage, default=None)
        description_regex = r'<div class="description fleft">.*?<p>\s*(.*?)\s*</p>.*?</div>'
        video['description'] = self._html_search_regex(description_regex, webpage, 'description', flags=DOTALL, default=None)
        for field in [
                ['duration', 'Durée du programme', '(\d+) min'],
                ['creator', 'Auteur\(s\)', '(.*?)'],
                ['release_date', 'Date de réalisation', '(.*?)'],
        ]:
            regex = r'<dd><span style="font-weight:bold;" >{0}</span> : {1} </dd>'.format(field[1], field[2])
            video[field[0]] = self._html_search_regex(regex, webpage, field[0], flags=DOTALL, default=None)
        video['duration'] = int_or_none(video['duration'], invscale=60)
        date = video['release_date'].split(' ')
        video["release_date"] = "{0}{1}{2}".format(date[2], month_by_name(unescapeHTML(date[1]).lower(), 'fr'), date[0])

        return video
