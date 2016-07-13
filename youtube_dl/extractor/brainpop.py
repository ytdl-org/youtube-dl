# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    remove_end
)


class BrainPOPIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:(.+)\.)?brainpop\.com\/[^/]+/[^/]+/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://www.brainpop.com/english/freemovies/williamshakespeare/',
        'md5': '676d936271b628dc05e4cec377751919',
        'info_dict': {
            'id': '3026',
            'display_id': 'williamshakespeare',
            'ext': 'mp4',
            'title': 'William Shakespeare',
            'thumbnail': 're:^https?://.*\.png$',
            'description': 'He could do comedies, tragedies, histories and poetry.  Learn about the greatest playwright in the history of the English language!',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        content = self._parse_json(self._html_search_regex(r'var content = ([^;]*)', webpage, 'content JSON'), display_id)
        topic = content['category']['unit']['topic']

        if topic['free'] == 'no':
            self.raise_login_required('%s is only available for users with Subscriptions' % display_id)

        global_content = self._parse_json(self._html_search_regex(r'var global_content = ([^;]*)', webpage, 'global content JSON').replace("'", '"'), display_id)
        cdn_path = global_content.get('cdn_path', 'https://cdn.brainpop.com')
        movie_cdn_path = global_content.get('movie_cdn_path', 'https://svideos.brainpop.com')
        ec_token = self._html_search_regex(r"ec_token : '([^']*)'", webpage, 'token')

        thumbnails = [{'url': cdn_path + screenshot} for screenshot in topic.get('screenshots', {})]

        movies = topic['movies']
        formats = []
        formats.append({
            'url': movie_cdn_path + movies['mp4'] + '?' + ec_token,
            'height': 768,
            'width': 768,
        })
        formats.append({
            'url': movie_cdn_path + movies['mp4_small'] + '?' + ec_token,
            'height': 480,
            'width': 480,
        })
        self._sort_formats(formats)

        settings = self._parse_json(self._html_search_regex(r'var settings = ([^;]*)', webpage, 'settings JSON', '{}'), display_id)

        return {
            'id': topic['EntryID'],
            'display_id': display_id,
            'title': remove_end(settings.get('title', display_id), ' - BrainPOP'),
            'description': settings.get('description', ''),
            'thumbnails': thumbnails,
            'formats': formats,
        }
