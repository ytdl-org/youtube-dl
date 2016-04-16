from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urlparse
from .internetvideoarchive import InternetVideoArchiveIE


class RottenTomatoesIE(InfoExtractor):
    _VALID_URL = r'https?://www\.rottentomatoes\.com/m/[^/]+/trailers/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.rottentomatoes.com/m/toy_story_3/trailers/11028566/',
        'info_dict': {
            'id': '613340',
            'ext': 'mp4',
            'title': 'Toy Story 3',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        og_video = self._og_search_video_url(webpage)
        query = compat_urlparse.urlparse(og_video).query

        return {
            '_type': 'url_transparent',
            'url': InternetVideoArchiveIE._build_xml_url(query),
            'ie_key': InternetVideoArchiveIE.ie_key(),
            'title': self._og_search_title(webpage),
        }
