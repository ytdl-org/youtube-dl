# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_parse_qs,
    compat_urllib_parse,
    remove_end,
)


class CloudyIE(InfoExtractor):
    _IE_DESC = 'cloudy.ec and videoraj.ch'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?(?P<host>cloudy\.ec|videoraj\.ch)/
        (?:v/|embed\.php\?id=)
        (?P<id>[A-Za-z0-9]+)
        '''
    _EMBED_URL = 'http://www.%s/embed.php?id=%s'
    _API_URL = 'http://www.%s/api/player.api.php?%s'
    _TESTS = [
        {
            'url': 'https://www.cloudy.ec/v/af511e2527aac',
            'md5': '5cb253ace826a42f35b4740539bedf07',
            'info_dict': {
                'id': 'af511e2527aac',
                'ext': 'flv',
                'title': 'Funny Cats and Animals Compilation june 2013',
            }
        },
        {
            'url': 'http://www.videoraj.ch/v/47f399fd8bb60',
            'md5': '7d0f8799d91efd4eda26587421c3c3b0',
            'info_dict': {
                'id': '47f399fd8bb60',
                'ext': 'flv',
                'title': 'Burning a New iPhone 5 with Gasoline - Will it Survive?',
            }
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_host = mobj.group('host')
        video_id = mobj.group('id')

        url = self._EMBED_URL % (video_host, video_id)
        webpage = self._download_webpage(url, video_id)

        file_key = self._search_regex(
            r'filekey\s*=\s*"([^"]+)"', webpage, 'file_key')
        data_url = self._API_URL % (video_host, compat_urllib_parse.urlencode({
            'file': video_id,
            'key': file_key,
        }))
        player_data = self._download_webpage(
            data_url, video_id, 'Downloading player data')
        data = compat_parse_qs(player_data)

        if 'error' in data:
            raise ExtractorError(
                '%s error: %s' % (self.IE_NAME, ' '.join(data['error_msg'])),
                expected=True)

        title = data.get('title', [None])[0]
        if title:
            title = remove_end(title, '&asdasdas').strip()

        formats = []
        video_url = data.get('url', [None])[0]
        if video_url:
            formats.append({
                'format_id': 'sd',
                'url': video_url,
            })

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }
