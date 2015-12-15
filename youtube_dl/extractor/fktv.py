from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    determine_ext,
    ExtractorError,
)


class FKTVIE(InfoExtractor):
    IE_NAME = 'fernsehkritik.tv'
    _VALID_URL = r'http://(?:www\.)?fernsehkritik\.tv/folge-(?P<id>[0-9]+)(?:/.*)?'

    _TEST = {
        'url': 'http://fernsehkritik.tv/folge-1',
        'md5': '21f0b0c99bce7d5b524eb1b17b1c6d79',
        'info_dict': {
            'id': '1',
            'ext': 'mp4',
            'title': 'Folge 1 vom 10. April 2007',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        episode = self._match_id(url)

        webpage = self._download_webpage(
            'http://fernsehkritik.tv/folge-%s/play' % episode, episode)
        title = clean_html(self._html_search_regex(
            '<h3>([^<]+)</h3>', webpage, 'title'))
        matches = re.search(
            r'(?s)<video(?:(?!poster)[^>])+(?:poster="([^"]+)")?[^>]*>(.*)</video>',
            webpage)
        if matches is None:
            raise ExtractorError('Unable to extract the video')

        poster, sources = matches.groups()
        if poster is None:
            self.report_warning('unable to extract thumbnail')

        urls = re.findall(r'<source[^>]+src="([^"]+)"', sources)
        formats = [{
            'url': furl,
            'format_id': determine_ext(furl),
        } for furl in urls]
        return {
            'id': episode,
            'title': title,
            'formats': formats,
            'thumbnail': poster,
        }
