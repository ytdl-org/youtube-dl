from __future__ import unicode_literals

import re
import time
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_duration,
)


class ClipfishIE(InfoExtractor):
    IE_NAME = 'clipfish'

    _VALID_URL = r'^https?://(?:www\.)?clipfish\.de/.*?/video/(?P<id>[0-9]+)/'
    _TEST = {
        'url': 'http://www.clipfish.de/special/game-trailer/video/3966754/fifa-14-e3-2013-trailer/',
        'md5': '2521cd644e862936cf2e698206e47385',
        'info_dict': {
            'id': '3966754',
            'ext': 'mp4',
            'title': 'FIFA 14 - E3 2013 Trailer',
            'duration': 82,
        },
        'skip': 'Blocked in the US'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)

        info_url = ('http://www.clipfish.de/devxml/videoinfo/%s?ts=%d' %
                    (video_id, int(time.time())))
        doc = self._download_xml(
            info_url, video_id, note='Downloading info page')
        title = doc.find('title').text
        video_url = doc.find('filename').text
        if video_url is None:
            xml_bytes = xml.etree.ElementTree.tostring(doc)
            raise ExtractorError('Cannot find video URL in document %r' %
                                 xml_bytes)
        thumbnail = doc.find('imageurl').text
        duration = parse_duration(doc.find('duration').text)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
            'duration': duration,
        }
