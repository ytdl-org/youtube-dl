from __future__ import unicode_literals

import re

from .zdf import ZDFIE


class DreiSatIE(ZDFIE):
    IE_NAME = '3sat'
    _VALID_URL = r'(?:https?://)?(?:www\.)?3sat\.de/mediathek/(?:index\.php|mediathek\.php)?\?(?:(?:mode|display)=[^&]+&)*obj=(?P<id>[0-9]+)$'
    _TESTS = [
        {
            'url': 'http://www.3sat.de/mediathek/index.php?mode=play&obj=45918',
            'md5': 'be37228896d30a88f315b638900a026e',
            'info_dict': {
                'id': '45918',
                'ext': 'mp4',
                'title': 'Waidmannsheil',
                'description': 'md5:cce00ca1d70e21425e72c86a98a56817',
                'uploader': 'SCHWEIZWEIT',
                'uploader_id': '100000210',
                'upload_date': '20140913'
            },
            'params': {
                'skip_download': True,  # m3u8 downloads
            }
        },
        {
            'url': 'http://www.3sat.de/mediathek/mediathek.php?mode=play&obj=51066',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        details_url = 'http://www.3sat.de/mediathek/xmlservice/web/beitragsDetails?ak=web&id=%s' % video_id
        return self.extract_from_xml_url(video_id, details_url)
