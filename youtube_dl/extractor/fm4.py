# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

# audios on fm4.orf.at are only available for 7 days, so we can't
# add tests.


class FM4IE(InfoExtractor):
    IE_DESC = 'fm4.orf.at'
    _VALID_URL = r'http://fm4\.orf\.at/7tage/?#(?P<date>[0-9]+)/(?P<show>\w+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        show_date = mobj.group('date')
        show_id = mobj.group('show')

        data = self._download_json(
            'http://audioapi.orf.at/fm4/json/2.0/broadcasts/%s/4%s' % (show_date, show_id),
            show_id
        )

        def extract_entry_dict(info, title, subtitle):
            return {
                'id': info['loopStreamId'].replace('.mp3', ''),
                'url': 'http://loopstream01.apa.at/?channel=fm4&id=%s' % info['loopStreamId'],
                'title': title,
                'description': subtitle,
                'duration': (info['end'] - info['start']) / 1000,
                'timestamp': info['start'] / 1000,
                'ext': 'mp3'
            }

        entries = [extract_entry_dict(t, data['title'], data['subtitle']) for t in data['streams']]

        return {
            '_type': 'playlist',
            'id': show_id,
            'title': data['title'],
            'description': data['subtitle'],
            'entries': entries
        }
