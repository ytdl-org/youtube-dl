import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import determine_ext

class CNNIE(InfoExtractor):
    _VALID_URL = r'https?://(edition\.)?cnn\.com/video/(data/.+?|\?)/(?P<path>.+?/(?P<title>[^/]+?)\.cnn)'

    _TEST = {
        u'url': u'http://edition.cnn.com/video/?/video/sports/2013/06/09/nadal-1-on-1.cnn',
        u'file': u'sports_2013_06_09_nadal-1-on-1.cnn.mp4',
        u'md5': u'3e6121ea48df7e2259fe73a0628605c4',
        u'info_dict': {
            u'title': u'Nadal wins 8th French Open title',
            u'description': u'World Sport\'s Amanda Davies chats with 2013 French Open champion Rafael Nadal.',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        path = mobj.group('path')
        page_title = mobj.group('title')
        info_xml = self._download_webpage(
            'http://cnn.com/video/data/3.0/%s/index.xml' % path, page_title)
        info = xml.etree.ElementTree.fromstring(info_xml.encode('utf-8'))

        formats = []
        for f in info.findall('files/file'):
            mf = re.match(r'(\d+)x(\d+)(?:_(.*)k)?',f.attrib['bitrate'])
            if mf is not None:
                formats.append((int(mf.group(1)), int(mf.group(2)), int(mf.group(3) or 0), f.text))
        formats = sorted(formats)
        (_,_,_, video_path) = formats[-1]
        video_url = 'http://ht.cdn.turner.com/cnn/big%s' % video_path

        thumbnails = sorted([((int(t.attrib['height']),int(t.attrib['width'])), t.text) for t in info.findall('images/image')])
        thumbs_dict = [{'resolution': res, 'url': t_url} for (res, t_url) in thumbnails]

        return {'id': info.attrib['id'],
                'title': info.find('headline').text,
                'url': video_url,
                'ext': determine_ext(video_url),
                'thumbnail': thumbnails[-1][1],
                'thumbnails': thumbs_dict,
                'description': info.find('description').text,
                }
