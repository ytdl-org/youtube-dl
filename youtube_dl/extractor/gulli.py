# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import parse_duration, get_element_by_class, get_element_by_id


class GulliIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?replay\.gulli\.fr/.+VOD(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://replay.gulli.fr/emissions/Wazup39/VOD69258840197000',
        'info_dict': {
            'id': '69258840197000',
            'ext': 'mp4',
            'title': 'Wazup - Mercredi 29/01/2020',
            'duration': 269,
            'description': "Le Magazine quotidien des 6-12 ans à la pointe de l'info culturelle ! 4min30 pour s'informer sur les tendances, les expositions, les sorties ciné, livres, spectacles, musique, mode... Le Wazup, c'est le meilleur de l'actu pour les enfants avec en prime des bonus inédits sur Gulli.fr.",
            'thumbnail': "https://resize-gulli.jnsmedia.fr/rcrop/748,420/img/var/storage/imports/replay/images/473769_0.jpg",
            'series': 'Wazup',
            'season_number': 6,
            'episode_number': 93,
            'episode': "Wazup - Mercredi 29/01/2020",
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'"name"\: "([^"]+)', webpage, 'title')
        thumbnail = self._html_search_regex(r'"thumbnailUrl"\: "([^"]+)', webpage, 'thumbnail', fatal=False)
        description = self._html_search_regex(r'<span id="episode_description">(.+?)</span>', webpage, 'description', fatal=False)
        duration = parse_duration(self._html_search_regex(r'"duration"\: "PT([^"]+)', webpage, 'duration', fatal=False))
        series = self._og_search_property('title', webpage)
        season_number = self._html_search_regex(r"'content_level_3': 's(\d+)e", webpage, 'season number', fatal=False)
        episode_number = self._html_search_regex(r"'content_level_3': 's\d+e(\d+)", webpage, 'episode number', fatal=False)
        episode = get_element_by_id('h1_episode_name', webpage)
        download_url = self._html_search_regex(r'"contentUrl"\: "([^"]+)', webpage, 'download url')

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'url': download_url,
            'duration': duration,
            'description': description,
            'series': series,
            'season_number': int(season_number),
            'episode_number': int(episode_number),
            'episode': episode,
        }


class GulliPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?replay\.gulli\.fr/.+/(?!VOD)(?P<id>[^/]+)(?!.+)'
    _TESTS = [{
        'url': 'https://replay.gulli.fr/dessins-animes/Beyblade-Burst-Turbo',
        'info_dict': {
            'id': 'Beyblade-Burst-Turbo',
            'title': 'Beyblade Burst',
        },
        'playlist_mincount': 3,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)
        entries = []
        bloc_html = get_element_by_class('bloc_listing', webpage)
        for mobj in re.finditer(r'<a[^>]+href=(["\'])(?P<url>%s.*?)\1[^>]*>' % GulliIE._VALID_URL, bloc_html):
            entries.append(self.url_result(mobj.group('url'), ie=GulliIE.ie_key()))

        title = self._html_search_regex(
            r'<h1>Regardez *(.+?)\n? *</h1>', webpage, 'playlist title',
            fatal=False)

        return self.playlist_result(entries, playlist_id, title)
