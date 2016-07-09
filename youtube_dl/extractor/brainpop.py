# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class BrainPOPIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:(.+)\.)?brainpop\.com\/(?P<id>[^\r\n]+)'
    _TEST = {
        'url': 'https://www.brainpop.com/english/freemovies/williamshakespeare/',
        'md5': '676d936271b628dc05e4cec377751919',
        'info_dict': {
            'id': 'english/freemovies/williamshakespeare/',
            'ext': 'mp4',
            'title': 'William Shakespeare - BrainPOP',
            'thumbnail': 're:^https?://.*\.png$',
            'description': 'He could do comedies, tragedies, histories and poetry.  Learn about the greatest playwright in the history of the English language!',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        ec_token = self._html_search_regex(r"ec_token : '([^']*)'", webpage, 'token')

        settings = self._parse_json(self._html_search_regex(r'var settings = ([^;]*)', webpage, 'settings'), video_id)
        title = settings['title']
        description = settings['description']

        global_content = self._parse_json(self._html_search_regex(r'var global_content = ([^;]*)', webpage, 'global content').replace("'", '"'), video_id)
        cdn_path = global_content['cdn_path']
        movie_cdn_path = global_content['movie_cdn_path']

        content = self._parse_json(self._html_search_regex(r'var content = ([^;]*)', webpage, 'content'), video_id)
        movies = content['category']['unit']['topic']['movies']
        screenshots = content['category']['unit']['topic']['screenshots']

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

        thumbnails = []
        for (i, screenshot) in enumerate(screenshots):
            thumbnails.append({
                'url': cdn_path + screenshot,
            })

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnails': thumbnails,
            'description': description,
        }
