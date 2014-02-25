from __future__ import unicode_literals

import re

from .common import InfoExtractor


class TruTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?trutube\.tv/video/(?P<id>[0-9]+)/.*'
    _TEST = {
        'url': 'http://trutube.tv/video/14880/Ramses-II-Proven-To-Be-A-Red-Headed-Caucasoid-',
        'md5': 'c5b6e301b0a2040b074746cbeaa26ca1',
        'info_dict': {
            'id': '14880',
            'ext': 'flv',
            'title': 'Ramses II - Proven To Be A Red Headed Caucasoid',
            'thumbnail': 're:^http:.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        video_title = self._og_search_title(webpage).strip()
        thumbnail = self._search_regex(
            r"var splash_img = '([^']+)';", webpage, 'thumbnail', fatal=False)

        all_formats = re.finditer(
            r"var (?P<key>[a-z]+)_video_file\s*=\s*'(?P<url>[^']+)';", webpage)
        formats = [{
            'format_id': m.group('key'),
            'quality': -i,
            'url': m.group('url'),
        } for i, m in enumerate(all_formats)]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'thumbnail': thumbnail,
        }
