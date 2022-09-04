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


class RadioFrancePodcastIE(InfoExtractor):
    _VALID_URL = r'https?://www\.radiofrance\.fr/(?:francemusique|franceinter|franceculture|franceinfo|mouv|fip)/podcasts/.*-(?P<id>\d+)$'

    _TESTS = [{
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
            'upload_date': str,
        }
    }, {
        'url': 'https://www.radiofrance.fr/francemusique/podcasts/allegretto/lever-du-jour-9233228',
        'only_matching': True,
    }, {
        'url': 'https://www.radiofrance.fr/franceinter/podcasts/rendez-vous-avec-x/un-mysterieux-echange-digne-de-la-guerre-froide-9343281',
        'only_matching': True,
    }, {
        'url': 'https://www.radiofrance.fr/franceculture/podcasts/la-science-cqfd/teotihuacan-la-plus-mysterieuse-des-cites-d-or-9224610',
        'only_matching': True,
    }, {
        'url': 'https://www.radiofrance.fr/mouv/podcasts/mouv-dj-la-caution/ncr2a-ne-cherche-rien-d-autre-ailleurs-1197950',
        'only_matching': True,
    }, {
        'url': 'https://www.radiofrance.fr/fip/podcasts/certains-l-aiment-fip/hommage-au-cinema-de-vangelis-4734742',
        'only_matching': True,
    }]

    def extract_api_data(self, id, html):
        pattern = r'<script [^>]*sveltekit:data-url="https://www\.radiofrance\.fr/api/v[\d.]+/path[^>]*>(?P<json>.*)</script>'
        json = self._search_regex(pattern, html, 'API data', flags=re.DOTALL, group='json')
        if json:
            json = self._parse_json(json, id)
            if json and 'body' in json:
                json = self._parse_json(json.get('body'), id)
        if not json:
            raise ExtractorError('%s: JSON data not found' % id)
        return json

    def _real_extract(self, url):
        media_id = self._match_id(url)
        webpage = self._download_webpage(url, media_id)

        api_data = self.extract_api_data(media_id, webpage)
        api_data = api_data['content']

        url = url_or_none(api_data['manifestations'][0]['url'])
        duration = int_or_none(api_data['manifestations'][0].get('duration'))

        title = strip_or_none(api_data.get('title'))
        title = title or strip_or_none(self._og_search_title(webpage))
        title = title or strip_or_none(get_element_by_attribute('h1', None, webpage, False))

        description = strip_or_none(api_data.get('standFirst'))
        description = description or strip_or_none(self._og_search_description(webpage))

        visual = api_data.get('visual')
        thumbnail = None
        if visual:
            thumbnail = url_or_none(visual.get('src'))
        if not thumbnail:
            thumbnail = self._og_search_thumbnail(webpage)

        channel_id = self._og_search_property('site_name', webpage, 'Station name', fatal=False)

        publication_time = parse_iso8601(self._html_search_meta('article:published_time', webpage, 'publication time', ))

        return {
            'id': media_id,
            'title': title,
            'url': url,
            'description': description,
            'thumbnail': thumbnail,
            'channel_id': channel_id,
            'timestamp': publication_time,
            'duration': duration,
            'is_live': False
        }
