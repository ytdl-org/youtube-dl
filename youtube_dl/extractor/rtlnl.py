from __future__ import unicode_literals

import re

from .common import InfoExtractor


class RtlXlIE(InfoExtractor):
    IE_NAME = 'rtlxl.nl'
    _VALID_URL = r'https?://www\.rtlxl\.nl/#!/[^/]+/(?P<uuid>[^/?]+)'

    _TEST = {
        'url': 'http://www.rtlxl.nl/#!/rtl-nieuws-132237/6e4203a6-0a5e-3596-8424-c599a59e0677',
        'info_dict': {
            'id': '6e4203a6-0a5e-3596-8424-c599a59e0677',
            'ext': 'flv',
            'title': 'RTL Nieuws - Laat',
            'description': 'Dagelijks het laatste nieuws uit binnen- en '
                'buitenland. Voor nog meer nieuws kunt u ook gebruikmaken van '
                'onze mobiele apps.',
            'timestamp': 1408051800,
            'upload_date': '20140814',
        },
        'params': {
            # We download the first bytes of the first fragment, it can't be
            # processed by the f4m downloader beacuse it isn't complete
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uuid = mobj.group('uuid')

        info = self._download_json(
            'http://www.rtl.nl/system/s4m/vfd/version=2/uuid=%s/fmt=flash/' % uuid,
            uuid)
        meta = info['meta']
        material = info['material'][0]
        episode_info = info['episodes'][0]

        f4m_url = 'http://manifest.us.rtl.nl' + material['videopath']
        progname = info['abstracts'][0]['name']
        subtitle = material['title'] or info['episodes'][0]['name']

        return {
            'id': uuid,
            'title': '%s - %s' % (progname, subtitle), 
            'formats': self._extract_f4m_formats(f4m_url, uuid),
            'timestamp': material['original_date'],
            'description': episode_info['synopsis'],
        }
