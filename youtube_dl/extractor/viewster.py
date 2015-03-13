from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_request


class ViewsterIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?viewster\.com/movie/(?P<id>\d+-\d+-\d+)'
    _TEST = {
        'url': 'http://www.viewster.com/movie/1293-19341-000/hout-wood/',
        'md5': '8f9d94b282d80c42b378dffdbb11caf3',
        'info_dict': {
            'id': '1293-19341-000',
            'ext': 'flv',
            'title': "'Hout' (Wood)",
            'description': 'md5:925733185a9242ef96f436937683f33b',
        },
    }

    _ACCEPT_HEADER = 'application/json, text/javascript, */*; q=0.01'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        request = compat_urllib_request.Request(
            'http://api.live.viewster.com/api/v1/movielink?movieid=%s&action=movierent&paymethod=fre&price=0&currency=&language=en&subtitlelanguage=x&ischromecast=false' % video_id)
        request.add_header('Accept', self._ACCEPT_HEADER)

        movie_link = self._download_json(
            request, video_id, 'Downloading movie link JSON')

        formats = self._extract_f4m_formats(
            movie_link['url'] + '&hdcore=3.2.0&plugin=flowplayer-3.2.0.1', video_id)
        self._sort_formats(formats)

        request = compat_urllib_request.Request(
            'http://api.live.viewster.com/api/v1/movie/%s' % video_id)
        request.add_header('Accept', self._ACCEPT_HEADER)

        movie = self._download_json(
            request, video_id, 'Downloading movie metadata JSON')

        title = movie.get('title') or movie['original_title']
        description = movie.get('synopsis')
        thumbnail = movie.get('large_artwork') or movie.get('artwork')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }
