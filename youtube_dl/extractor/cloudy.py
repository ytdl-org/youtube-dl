# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_parse_qs,
    compat_urllib_parse,
)


class CloudyIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?cloudy\.ec/
        (?:v/|embed\.php\?id=)
        (?P<id>[A-Za-z0-9]+)
        '''
    _API_URL = 'http://www.cloudy.ec/api/player.api.php?%s'
    _TEST = {
        'url': 'https://www.cloudy.ec/v/af511e2527aac',
        'md5': '5cb253ace826a42f35b4740539bedf07',
        'info_dict': {
            'id': 'af511e2527aac',
            'ext': 'flv',
            'title': 'Funny Cats and Animals Compilation june 2013',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        url = 'http://www.cloudy.ec/embed.php?id=%s' % video_id
        webpage = self._download_webpage(url, video_id)

        file_key = self._search_regex(
            r'filekey\s*=\s*"([^"]+)"', webpage, 'file_key')
        data_url = self._API_URL % compat_urllib_parse.urlencode({
            'file': video_id,
            'key': file_key,
        })
        player_data = self._download_webpage(
            data_url, video_id, 'Downloading player data')
        data = compat_parse_qs(player_data)

        if 'error' in data:
            raise ExtractorError(
                '%s error: %s' % (self.IE_NAME, ' '.join(data['error_msg'])),
                expected=True)

        title = data.get('title', [None])[0]
        if title:
            title = title.replace('&asdasdas', '').strip()

        formats = []
        formats.append({
            'format_id': 'sd',
            'url': data.get('url', [None])[0],
        })

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }
