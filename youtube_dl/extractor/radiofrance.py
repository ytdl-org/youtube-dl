# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    get_element_by_attribute,
    int_or_none,
    parse_iso8601,
    strip_or_none,
    url_or_none
)


class RadioFranceBaseIE(InfoExtractor):
    _BASE_URL = r'https://www.radiofrance.fr/'

    def extract_api_data(self, id, html):
        pattern = r'<script [^>]*sveltekit:data-url="https://www\.radiofrance\.fr/api/v[\d.]+/path[^>]*>(?P<json>.*)</script>'
        json = self._search_regex(pattern, html, 'API data', flags=re.DOTALL, group='json')
        if not json:
            raise ExtractorError('%s: JSON data not found' % id)

        try:
            json = self._parse_json(json, id)
            json = self._parse_json(json['body'], id)
            return json['content']
        except KeyError:
            raise ExtractorError('%s: Invalid JSON' % id)

    def parse_api_data_info(self, api_data):
        title = strip_or_none(api_data.get('title'))
        description = strip_or_none(api_data.get('standFirst'))
        channel_id = strip_or_none(api_data.get('brand'))
        visual = api_data.get('visual')
        publication_time = api_data.get('publishedDate')
        thumbnail = None
        if visual:
            thumbnail = url_or_none(visual.get('src'))

        return {
            'title': title,
            'description': description,
            'channel_id': channel_id,
            'thumbnail': thumbnail,
            'timestamp': publication_time,
        }

    def parse_html_info(self, webpage):
        title = strip_or_none(self._og_search_title(webpage)) or strip_or_none(get_element_by_attribute('h1', None, webpage, False))
        description = strip_or_none(self._og_search_description(webpage))
        thumbnail = self._og_search_thumbnail(webpage)
        channel_id = self._og_search_property('site_name', webpage, 'Station name', fatal=False)
        publication_time = parse_iso8601(self._html_search_meta('article:published_time', webpage, 'publication time', ))

        return {
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'channel_id': channel_id,
            'timestamp': publication_time
        }

    def extract_episode(self, episode_id, api_data):
        manifestations = api_data.get('manifestations')
        if manifestations is None or len(manifestations) == 0:
            return None

        url = url_or_none(manifestations[0]['url'])
        duration = int_or_none(manifestations[0].get('duration'))
        episode_info = {
                'id': episode_id,
                'url': url,
                'duration': duration
            }
        return self.parse_api_data_info(api_data) | episode_info

    def extract_playlist_entries(self, url, playlist_id, api_data, direction):
        playlist_data = api_data['expressions']

        entries = []
        items = playlist_data.get('items')
        for item in items:
            episode_path = item.get('path')
            if episode_path is None:
                self.report_warning('No path found for episode "%s"', item.get('title'))
                continue
            episode_id = RadioFrancePodcastEpisodeIE._match_id(self._BASE_URL + item.get('path'))
            if episode_id is None:
                self.report_warning('Could not parse id of episode from path: "%s"' % item.get('path'))
                continue
            entry = self.extract_episode(episode_id,  item)
            if entry is None:
                msg = 'Podcast file is not available. If the show is too recent, the file may not have been uploaded yet: try again later.'
                self.to_screen('Episode "%s" is not available' % episode_path)
                continue
            entries.append(entry)

        page_number = int_or_none(playlist_data.get('pageNumber'))
        if page_number:
            if direction in ['both', 'prev'] and playlist_data.get('prev') is not None:
                webpage, other_api_data = self.get_data(url, playlist_id, page=page_number - 1)
                entries = self.extract_playlist_entries(url, playlist_id, other_api_data, direction='prev') + entries
            if direction in ['both', 'next'] and playlist_data.get('next') is not None:
                webpage, other_api_data = self.get_data(url, playlist_id, page=page_number + 1)
                entries = entries + self.extract_playlist_entries(url, playlist_id, other_api_data, direction='next')

        return entries

    def extract_playlist(self, playlist_id, url, api_data):
        entries = self.extract_playlist_entries(url, playlist_id, api_data, direction='both')
        entries = list(filter(lambda e: e is not None, entries))
        entries.reverse()
        playlist_info = {
            '_type': 'playlist',
            'id': playlist_id,
            'entries': entries
        }
        return self.parse_api_data_info(api_data) | playlist_info

    def get_data(self, url, id, page=None):
        query = {}
        note = None
        if page:
            query['p'] = page
            note = "Downloading page %i" % page
        webpage = self._download_webpage(url, id, query=query, note=note)
        api_data = self.extract_api_data(id, webpage)
        return webpage, api_data


class RadioFrancePodcastEpisodeIE(RadioFranceBaseIE):
    _VALID_URL = r'https?://www\.radiofrance\.fr/(?:francemusique|franceinter|franceculture|franceinfo|mouv|fip)/podcasts/.+/.+-(?P<id>\d+)$'

    _TESTS = [{
        'note': 'Podcast episode with audio from France Info',
        'url': 'https://www.radiofrance.fr/franceinfo/podcasts/le-brief-eco/le-brief-eco-du-lundi-05-septembre-2022-8310713',
        'info_dict': {
            'id': '8310713',
            'ext': 'mp3',
            'url': r're:^https?://.*\.mp3$',
            'title': 'Pour la première fois en vingt ans, l’euro passe sous les 0,99\u00a0dollar',
            'description': str,
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': int,
            'duration': int,
            'upload_date': str
        }
    }, {
        'note': 'Podcast episode from France Musique',
        'url': 'https://www.radiofrance.fr/francemusique/podcasts/allegretto/lever-du-jour-9233228',
        'only_matching': True
    }, {
        'note': 'Podcast episode from FranceInter',
        'url': 'https://www.radiofrance.fr/franceinter/podcasts/rendez-vous-avec-x/un-mysterieux-echange-digne-de-la-guerre-froide-9343281',
        'only_matching': True
    }, {
        'note': 'Podcast episode from France Culture',
        'url': 'https://www.radiofrance.fr/franceculture/podcasts/la-science-cqfd/teotihuacan-la-plus-mysterieuse-des-cites-d-or-9224610',
        'only_matching': True
    }, {
        'note': 'Podcast episode from Le Mouv',
        'url': 'https://www.radiofrance.fr/mouv/podcasts/mouv-dj-la-caution/ncr2a-ne-cherche-rien-d-autre-ailleurs-1197950',
        'only_matching': True
    }, {
        'note': 'Podcast episode from FIP',
        'url': 'https://www.radiofrance.fr/fip/podcasts/certains-l-aiment-fip/hommage-au-cinema-de-vangelis-4734742',
        'only_matching': True
    }]

    def _real_extract(self, url):
        id = self._match_id(url)
        webpage, api_data = self.get_data(url, id)
        api_data_info = self.extract_episode(id, api_data)
        if api_data_info is None:
            msg = 'Podcast file is not available. If the show is too recent, the file may not have been uploaded yet: try again later.'
            raise ExtractorError(msg, expected=True, video_id=id)

        html_info = self.parse_html_info(webpage)
        return html_info | api_data_info


class RadioFrancePodcastPlaylistIE(RadioFranceBaseIE):
    _VALID_URL = r'https?://www\.radiofrance\.fr/(?:francemusique|franceinter|franceculture|franceinfo|mouv|fip)/podcasts/(?P<id>[^/]+?)(?:[?#].*)?$'

    _TESTS = [{
        'note': 'Podcast show with multiple pages of episodes and some of them are missing',
        'url': 'https://www.radiofrance.fr/franceculture/podcasts/une-semaine-dans-le-monde-10-11?p=2',
        'info_dict': {
            'id': 'une-semaine-dans-le-monde-10-11',
            'title': 'Une semaine dans le monde | 10-11',
            'description': str,
            'timestamp': int
        },
        'playlist_count': 23,
    }]

    def _real_extract(self, url):
        id = self._match_id(url)
        webpage, api_data = self.get_data(url, id)

        html_info = self.parse_html_info(webpage)
        return html_info | self.extract_playlist(id, url, api_data)
