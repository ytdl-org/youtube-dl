import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import determine_ext


class CNNIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://((edition|www)\.)?cnn\.com/video/(data/.+?|\?)/
        (?P<path>.+?/(?P<title>[^/]+?)(?:\.cnn|(?=&)))'''

    _TESTS = [{
        u'url': u'http://edition.cnn.com/video/?/video/sports/2013/06/09/nadal-1-on-1.cnn',
        u'file': u'sports_2013_06_09_nadal-1-on-1.cnn.mp4',
        u'md5': u'3e6121ea48df7e2259fe73a0628605c4',
        u'info_dict': {
            u'title': u'Nadal wins 8th French Open title',
            u'description': u'World Sport\'s Amanda Davies chats with 2013 French Open champion Rafael Nadal.',
        },
    },
    {
        u"url": u"http://edition.cnn.com/video/?/video/us/2013/08/21/sot-student-gives-epic-speech.georgia-institute-of-technology&utm_source=feedburner&utm_medium=feed&utm_campaign=Feed%3A+rss%2Fcnn_topstories+%28RSS%3A+Top+Stories%29",
        u"file": u"us_2013_08_21_sot-student-gives-epic-speech.georgia-institute-of-technology.mp4",
        u"md5": u"b5cc60c60a3477d185af8f19a2a26f4e",
        u"info_dict": {
            u"title": "Student's epic speech stuns new freshmen",
            u"description": "A Georgia Tech student welcomes the incoming freshmen with an epic speech backed by music from \"2001: A Space Odyssey.\""
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        path = mobj.group('path')
        page_title = mobj.group('title')
        info_url = u'http://cnn.com/video/data/3.0/%s/index.xml' % path
        info_xml = self._download_webpage(info_url, page_title)
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
