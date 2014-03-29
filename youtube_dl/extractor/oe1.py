# coding: utf-8
from __future__ import unicode_literals

import calendar
import datetime
import re

from .common import InfoExtractor

# audios on oe1.orf.at are only available for 7 days, so we can't
# add tests.


class OE1IE(InfoExtractor):
    IE_DESC = 'oe1.orf.at'
    _VALID_URL = r'http://oe1\.orf\.at/programm/(?P<id>[0-9]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        show_id = mobj.group('id')

        data = self._download_json(
            'http://oe1.orf.at/programm/%s/konsole' % show_id,
            show_id
        )

        timestamp = datetime.datetime.strptime('%s %s' % (
            data['item']['day_label'],
            data['item']['time']
        ), '%d.%m.%Y %H:%M')
        unix_timestamp = calendar.timegm(timestamp.utctimetuple())

        return {
            'id': show_id,
            'title': data['item']['title'],
            'url': data['item']['url_stream'],
            'ext': 'mp3',
            'description': data['item'].get('info'),
            'timestamp': unix_timestamp
        }
