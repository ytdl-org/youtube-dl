import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import find_xpath_attr, compat_str


class NBCNewsIE(InfoExtractor):
    _VALID_URL = r'https?://www\.nbcnews\.com/video/.+?/(?P<id>\d+)'

    _TEST = {
        u'url': u'http://www.nbcnews.com/video/nbc-news/52753292',
        u'file': u'52753292.flv',
        u'md5': u'47abaac93c6eaf9ad37ee6c4463a5179',
        u'info_dict': {
            u'title': u'Crew emerges after four-month Mars food study',
            u'description': u'md5:24e632ffac72b35f8b67a12d1b6ddfc1',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        info_xml = self._download_webpage('http://www.nbcnews.com/id/%s/displaymode/1219' % video_id, video_id)
        info = xml.etree.ElementTree.fromstring(info_xml.encode('utf-8')).find('video')

        return {'id': video_id,
                'title': info.find('headline').text,
                'ext': 'flv',
                'url': find_xpath_attr(info, 'media', 'type', 'flashVideo').text,
                'description': compat_str(info.find('caption').text),
                'thumbnail': find_xpath_attr(info, 'media', 'type', 'thumbnail').text,
                }
