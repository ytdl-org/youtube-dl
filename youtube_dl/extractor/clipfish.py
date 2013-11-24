import re
import time
import xml.etree.ElementTree

from .common import InfoExtractor


class ClipfishIE(InfoExtractor):
    IE_NAME = u'clipfish'

    _VALID_URL = r'^https?://(?:www\.)?clipfish\.de/.*?/video/(?P<id>[0-9]+)/'
    _TEST = {
        u'url': u'http://www.clipfish.de/special/supertalent/video/4028320/supertalent-2013-ivana-opacak-singt-nobodys-perfect/',
        u'file': u'4028320.f4v',
        u'md5': u'5e38bda8c329fbfb42be0386a3f5a382',
        u'info_dict': {
            u'title': u'Supertalent 2013: Ivana Opacak singt Nobody\'s Perfect',
            u'duration': 399,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)

        info_url = ('http://www.clipfish.de/devxml/videoinfo/%s?ts=%d' %
                    (video_id, int(time.time())))
        info_xml = self._download_webpage(
            info_url, video_id, note=u'Downloading info page')
        doc = xml.etree.ElementTree.fromstring(info_xml)
        title = doc.find('title').text
        video_url = doc.find('filename').text
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
