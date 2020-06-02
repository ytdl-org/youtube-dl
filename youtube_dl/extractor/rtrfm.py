from __future__ import unicode_literals

from .common import InfoExtractor

from ..compat import compat_urllib_parse_urlencode
from ..compat import compat_urlparse

from ..utils import ExtractorError

import re


class RTRFMIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rtrfm.com.au/(?:shows/(?P<show1>[^/]+)|show-episode/(?P<show2>[^-]+)-(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})/?)'
    _SHOW_DATE_TITLE = r"window\.vm\.playShow\('([^']+)', *'([0-9]{4}-[0-9]{2}-[0-9]{2})', *'([^']+)'\)"
    _RESTREAMS_URL = 'https://restreams.rtrfm.com.au/rzz'
    _TESTS = [
        {
            'url': 'https://rtrfm.com.au/show-episode/breakfast-2020-06-01/',
            'md5': '594027f513ec36a24b15d65007a24dff',
            'info_dict': {
                'id': 'breakfast-2020-06-01',
                'ext': 'mp3',
                'title': 'Breakfast with Taylah 2020-06-01',
            },
        }
    ]

    def _real_extract(self, url):
        show1, show2, date = self._VALID_URL_RE.match(url).groups()
        webpage = self._download_webpage(url, show1 or show2)
        match = re.compile(self._SHOW_DATE_TITLE).search(webpage)
        if not match:
            raise ExtractorError('Error getting the show, date & title', expected=True)
        show, date, title = match.groups()
        query = {'n': show, 'd': date}
        query = compat_urllib_parse_urlencode(query)
        url = compat_urlparse.urlparse(self._RESTREAMS_URL)
        url = compat_urlparse.urlunparse(url._replace(query=query))
        url = self._download_json(url, show, 'Downloading MP3 URL')['u']
        return {
            'id': '%s-%s' % (show, date),
            'title': '%s %s' % (title, date),
            'url': url,
            'ext': 'mp3',
            'release_date': 'date',
            'description': self._og_search_description(webpage),
        }
