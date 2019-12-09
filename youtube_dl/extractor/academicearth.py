from __future__ import unicode_literals

import re

from .common import InfoExtractor


class AcademicEarthCourseIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?academicearth\.org/playlists/(?P<id>[^?#/]+)'
    IE_NAME = 'AcademicEarth:Course'
    _TESTS = [{
        'url': 'http://academicearth.org/playlists/laws-of-nature/',
        'info_dict': {
            'id': 'laws-of-nature',
            'title': 'Laws of Nature',
            'description': 'Introduce yourself to the laws of nature with these free online college lectures from Yale, Harvard, and MIT.',
        },
        'playlist_count': 3,
    }, {
        'url': "https://academicearth.org/playlists/first-day-of-freshman-year/",
        'info_dict': {
            'id': 'first-day-of-freshman-year',
            'title': 'FIRST DAY OF FRESHMAN YEAR',
            'description': 'Relive the first day of your freshman year with a series of first lectures from introductory college courses at MIT, Yale, and Stanford.'
        },
        'playlist_count': 3,
    }, {
        'url': 'https://academicearth.org/playlists/financial-crisis',
        'info_dict': {
            'id': 'financial-crisis',
            'title': 'UNDERSTANDING THE FINANCIAL CRISIS',
            'description': 'Expert perspectives on the Financial Crisis and how to manage it.'        
        },
        'playlist_count': 7,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)
        title = self._html_search_regex(
            r'<h1 class="playlist-name"[^>]*?>(.*?)</h1>', webpage, 'title')
        description = self._html_search_regex(
            r'<p class="excerpt"[^>]*?>(.*?)</p>',
            webpage, 'description', fatal=False)
        urls = re.findall(
            r'<li class="lecture-preview">\s*?<a target="_blank" href="([^"]+)">',
            webpage)
        entries = [self.url_result(u) for u in urls]

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': title,
            'description': description,
            'entries': entries,
        }
