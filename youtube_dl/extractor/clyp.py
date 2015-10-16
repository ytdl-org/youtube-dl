# coding: utf-8

from __future__ import unicode_literals

import re

from .common import InfoExtractor


class ClypIE(InfoExtractor):
    _VALID_URL = r'https://clyp\.it/........'

    _TESTS = [{
        'url': 'https://clyp.it/ojz2wfah',
        'md5': '1d4961036c41247ecfdcc439c0cddcbb',
        'info_dict': {
            'id': 'ojz2wfah',
            'ext': 'mp3',
            'title': 'Krisson80 - bits wip wip',
            'description': '#Krisson80BitsWipWip #chiptune\n#wip',
        },
    }, {
        'url': 'https://clyp.it/ojz2wfah',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = url.replace("https://clyp.it/", "")
        api_url = 'https://api.clyp.it/' + video_id
        metadata = self._download_json(api_url, video_id)

        title = metadata['Title']
        description = metadata['Description']
        duration = int(metadata['Duration'])
        
        formats = [
            {
            'url': metadata['OggUrl'],
            'format_id': 'ogg',
            'preference': -2
            },{
            'url': metadata['Mp3Url'],
            'format_id': 'mp3',
            'preference': -1
            }]

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'duration': duration
        }
