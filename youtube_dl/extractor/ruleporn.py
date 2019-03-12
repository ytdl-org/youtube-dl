from __future__ import unicode_literals

from .common import InfoExtractor


class RulePornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ruleporn\.com/(?:[^/?#&]+/)*(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'http://ruleporn.com/brunette-nympho-chick-takes-her-boyfriend-in-every-angle/',
        'md5': '86861ebc624a1097c7c10eaf06d7d505',
        'info_dict': {
            'id': '48212',
            'display_id': 'brunette-nympho-chick-takes-her-boyfriend-in-every-angle',
            'ext': 'mp4',
            'title': 'Brunette Nympho Chick Takes Her Boyfriend In Every Angle',
            'description': 'md5:6d28be231b981fff1981deaaa03a04d5',
            'age_limit': 18,
            'duration': 635.1,
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        url = self._search_regex(
            r'<source[^>]+src="(https?://media.ruleporn.com/media/videos/[a-zA-Z0-9/]+\.mp4)[^>]+>',
            webpage, 'url')

        title = self._search_regex(
            r'<h1>(.+?)</h1>',
            webpage, 'title')
        description = self._html_search_meta('description', webpage)

        return {
            'id': display_id,
            'title': title,
            'description': description,
            'age_limit': 18,
            'url': url
        }
