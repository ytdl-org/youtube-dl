from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class RedTubeIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?redtube\.com/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.redtube.com/66418',
        'md5': '7b8c22b5e7098a3e1c09709df1126d2d',
        'info_dict': {
            'id': '66418',
            'ext': 'mp4',
            'title': 'Sucked on a toilet',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if any(s in webpage for s in ['video-deleted-info', '>This video has been removed']):
            raise ExtractorError('Video %s has been removed' % video_id, expected=True)

        video_url = self._html_search_regex(
            r'<source src="(.+?)" type="video/mp4">', webpage, 'video URL')
        video_title = self._html_search_regex(
            r'<h1 class="videoTitle[^"]*">(.+?)</h1>',
            webpage, 'title')
        video_thumbnail = self._og_search_thumbnail(webpage)

        # No self-labeling, but they describe themselves as
        # "Home of Videos Porno"
        age_limit = 18

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': video_title,
            'thumbnail': video_thumbnail,
            'age_limit': age_limit,
        }
