import re
import time
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import ExtractorError


class ClipfishIE(InfoExtractor):
    IE_NAME = u'clipfish'

    _VALID_URL = r'^https?://(?:www\.)?clipfish\.de/.*?/video/(?P<id>[0-9]+)/'
    _TEST = {
        u'url': u'http://www.clipfish.de/special/game-trailer/video/3966754/fifa-14-e3-2013-trailer/',
        u'file': u'3966754.mp4',
        u'md5': u'2521cd644e862936cf2e698206e47385',
        u'info_dict': {
            u'title': u'FIFA 14 - E3 2013 Trailer',
            u'duration': 82,
        },
        u'skip': 'Blocked in the US'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)

        info_url = ('http://www.clipfish.de/devxml/videoinfo/%s?ts=%d' %
                    (video_id, int(time.time())))
        doc = self._download_xml(
            info_url, video_id, note=u'Downloading info page')
        title = doc.find('title').text
        video_url = doc.find('filename').text
        if video_url is None:
            xml_bytes = xml.etree.ElementTree.tostring(doc)
            raise ExtractorError(u'Cannot find video URL in document %r' %
                                 xml_bytes)
        thumbnail = doc.find('imageurl').text
        duration_str = doc.find('duration').text
        m = re.match(
            r'^(?P<hours>[0-9]+):(?P<minutes>[0-9]{2}):(?P<seconds>[0-9]{2}):(?P<ms>[0-9]*)$',
            duration_str)
        if m:
            duration = (
                (int(m.group('hours')) * 60 * 60) +
                (int(m.group('minutes')) * 60) +
                (int(m.group('seconds')))
            )
        else:
            duration = None

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
            'duration': duration,
        }
