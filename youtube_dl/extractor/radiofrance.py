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

    def extract_api_data(self, api_path, id, html):
        pattern = r'<script [^>]*sveltekit:data-url="https://www\.radiofrance\.fr/api/v[\d.]+/%s[^>]*>(?P<json>.*)</script>' % api_path
        json = self._search_regex(pattern, html, 'API data', flags=re.DOTALL, group='json')

        if not json:
            raise ExtractorError('%s: JSON data not found' % id)

        try:
            json = self._parse_json(json, id)
            json = self._parse_json(json['body'], id)

            if api_path == 'path':
                return json['content']
            elif api_path == 'stations':
                return json
            else:
                raise ExtractorError('Coding error')
        except KeyError:
            raise ExtractorError('%s: Invalid JSON' % id)

    def get_title(self, api_data, webpage=None):
        title = strip_or_none(api_data.get('title'))
        if not title and webpage:
            title = strip_or_none(get_element_by_attribute('h1', None, webpage, False)) or strip_or_none(self._og_search_title(webpage))
        return title

    def get_description(self, api_data, webpage=None):
        description = strip_or_none(api_data.get('standFirst'))
        if not description and webpage:
            description = strip_or_none(self._og_search_description(webpage))
        return description

    def get_thumbnail(self, api_data, webpage=None):
        thumbnail = None
        visual = api_data.get('visual')
        if visual:
            thumbnail = url_or_none(visual.get('src'))
        if not thumbnail and webpage:
            thumbnail = self._og_search_thumbnail(webpage)
        return thumbnail

    def get_timestamp(self, api_data, webpage=None):
        timestamp = api_data.get('publishedDate')
        if not timestamp and webpage:
            timestamp = parse_iso8601(self._html_search_meta('article:published_time', webpage, 'publication time', ))
        return timestamp

    def get_brand(self, api_data, webpage=None):
        brand = strip_or_none(api_data.get('brand'))
        if not brand and webpage:
            brand = self._og_search_property('site_name', webpage, 'Station name', fatal=False)
        return brand

    def extract_episode(self, episode_id, api_data):
        manifestations = api_data.get('manifestations')
        if manifestations is None or len(manifestations) == 0:
            return None, None

        url = url_or_none(manifestations[0]['url'])
        duration = int_or_none(manifestations[0].get('duration'))
        return url, duration

    def get_playlist_entries(self, playlist_url, playlist_id, api_data, direction):
        playlist_data = api_data['expressions']

        entries = []
        items = playlist_data.get('items')
        for item in items:
            episode_path = item.get('path')
            if episode_path is None:
                self.report_warning('No path found for episode "%s"', item.get('title'))
                continue
            episode_id = RadioFrancePodcastEpisodeIE._match_id(self._BASE_URL + episode_path)
            if episode_id is None:
                self.report_warning('Could not parse id of episode from path: "%s"' % episode_path)
                continue
            episode_url, duration = self.extract_episode(episode_id, item)
            if episode_url is None:
                self.to_screen('Episode "%s" is not available' % episode_path)
                continue
            entry = {
                'id': episode_id,
                'url': episode_url,
                'title': self.get_title(item),
                'description': self.get_description(item),
                'timestamp': self.get_timestamp(item),
                'thumbnail': self.get_thumbnail(item),
                'duration': duration,
            }
            entries.append(entry)

        page_number = int_or_none(playlist_data.get('pageNumber'))
        if page_number:
            if direction in ['both', 'prev'] and playlist_data.get('prev') is not None:
                webpage, other_api_data = self.get_data(playlist_url, 'path', playlist_id, page=page_number - 1)
                entries = self.get_playlist_entries(playlist_url, playlist_id, other_api_data, direction='prev') + entries
            if direction in ['both', 'next'] and playlist_data.get('next') is not None:
                webpage, other_api_data = self.get_data(playlist_url, 'path', playlist_id, page=page_number + 1)
                entries = entries + self.get_playlist_entries(playlist_url, playlist_id, other_api_data, direction='next')

        return entries

    def get_data(self, url, api_path, id, page=None):
        query = {}
        note = None
        if page:
            query['p'] = page
            note = "Downloading page %i" % page
        webpage = self._download_webpage(url, id, query=query, note=note)
        api_data = self.extract_api_data(api_path, id, webpage)
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
        webpage, api_data = self.get_data(url, 'path', id)
        url, duration = self.extract_episode(id, api_data)
        if url is None:
            msg = 'Podcast file is not available. If the show is too recent, the file may not have been uploaded yet: try again later.'
            raise ExtractorError(msg, expected=True, video_id=id)

        return {
            'id': id,
            'url': url,
            'title': self.get_title(api_data, webpage),
            'description': self.get_description(api_data, webpage),
            'timestamp': self.get_timestamp(api_data, webpage),
            'thumbnail': self.get_thumbnail(api_data, webpage),
            'channel_id': self.get_brand(api_data, webpage),
            'duration': duration,
        }


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
        webpage, api_data = self.get_data(url, 'path', id)

        entries = self.get_playlist_entries(url, id, api_data, direction='both')
        entries.reverse()

        return {
            'id': id,
            '_type': 'playlist',
            'entries': entries,
            'title': self.get_title(api_data, webpage),
            'description': self.get_description(api_data, webpage),
            'timestamp': self.get_timestamp(api_data, webpage),
            'thumbnail': self.get_thumbnail(api_data, webpage),
            'channel_id': self.get_brand(api_data, webpage),
        }


class RadioFranceWebradioIE(RadioFranceBaseIE):
    _VALID_URL = r'https?://www\.radiofrance\.fr/(?:francemusique|franceinter|franceculture|franceinfo|mouv|fip)/(?P<id>radio-[^/]+)$'

    _TESTS = [{
        'note': 'Full list of webradios available at https://www.radiofrance.fr/ecouter-musique',
        'url': 'https://www.radiofrance.fr/fip/radio-metal',
        'info_dict': {
            'id': 'radio-metal',
            'ext': 'aac',
            'title': str,
        },
        'params': {
            'format': 'aac',
            'skip_download': True,
        }
    }]

    def get_livestream_formats(self, id, api_data):
        sources = api_data['media']['sources']

        formats = []
        for source in sources:
            url = source.get('url')
            if not url:
                continue

            format_id = source.get('format')
            format = {
                'url': url,
                'format_id': format_id,
                'asr': 48000,
                'vcodec': 'none'
            }
            if format_id == 'mp3':
                format['preference'] = 1
                format['acodec'] = 'mp3'
                format['abr'] = source.get('bitrate')
            elif format_id == 'aac':
                format['preference'] = 2
                format['acodec'] = 'aac'
                format['abr'] = source.get('bitrate')
            elif format_id == 'hls':
                format['preference'] = 0
                format['manifest_url'] = url
            formats.append(format)

        if len(formats) == 0:
            raise ExtractorError('No live streaming URL found')
        return formats

    def _real_extract(self, url):
        id = self._match_id(url)
        webpage, api_data = self.get_data(url, 'stations', id)

        return {
            'id': id,
            'title': self.get_title(api_data, webpage),
            'formats': self.get_livestream_formats(id, api_data),
            'thumbnail': self.get_thumbnail(api_data, webpage),
            'channel_id': self.get_brand(api_data, webpage),
            'is_live': True
        }
