from __future__ import unicode_literals

import json

from .common import InfoExtractor


class RadioDeIE(InfoExtractor):
    IE_NAME = 'radio.de'
    _VALID_URL = r'https?://(?P<id>.+?)\.(?:radio\.(?:de|at|fr|pt|es|pl|it)|rad\.io)'
    _TEST = {
        'url': 'http://ndr2.radio.de/',
        'md5': '3b4cdd011bc59174596b6145cda474a4',
        'info_dict': {
            'id': 'ndr2',
            'ext': 'mp3',
            'title': 're:^NDR 2 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'md5:591c49c702db1a33751625ebfb67f273',
            'thumbnail': 're:^https?://.*\.png',
        },
        'params': {
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        radio_id = self._match_id(url)

        webpage = self._download_webpage(url, radio_id)

        broadcast = json.loads(self._search_regex(
            r'_getBroadcast\s*=\s*function\(\s*\)\s*{\s*return\s+({.+?})\s*;\s*}',
            webpage, 'broadcast'))

        title = self._live_title(broadcast['name'])
        description = broadcast.get('description') or broadcast.get('shortDescription')
        thumbnail = broadcast.get('picture4Url') or broadcast.get('picture4TransUrl')

        formats = [{
            'url': stream['streamUrl'],
            'ext': stream['streamContentFormat'].lower(),
            'acodec': stream['streamContentFormat'],
            'abr': stream['bitRate'],
            'asr': stream['sampleRate']
        } for stream in broadcast['streamUrls']]
        self._sort_formats(formats)

        return {
            'id': radio_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'is_live': True,
            'formats': formats,
        }
