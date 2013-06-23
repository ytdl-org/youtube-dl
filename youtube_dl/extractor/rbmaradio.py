import json
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse,

    ExtractorError,
)


class RBMARadioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rbmaradio\.com/shows/(?P<videoID>[^/]+)$'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        webpage = self._download_webpage(url, video_id)

        json_data = self._search_regex(r'window\.gon.*?gon\.show=(.+?);$',
            webpage, u'json data', flags=re.MULTILINE)

        try:
            data = json.loads(json_data)
        except ValueError as e:
            raise ExtractorError(u'Invalid JSON: ' + str(e))

        video_url = data['akamai_url'] + '&cbr=256'
        url_parts = compat_urllib_parse_urlparse(video_url)
        video_ext = url_parts.path.rpartition('.')[2]
        info = {
                'id': video_id,
                'url': video_url,
                'ext': video_ext,
                'title': data['title'],
                'description': data.get('teaser_text'),
                'location': data.get('country_of_origin'),
                'uploader': data.get('host', {}).get('name'),
                'uploader_id': data.get('host', {}).get('slug'),
                'thumbnail': data.get('image', {}).get('large_url_2x'),
                'duration': data.get('duration'),
        }
        return [info]
