import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,

    ExtractorError,
)

class GametrailersIE(InfoExtractor):
    _VALID_URL = r'http://www.gametrailers.com/(?P<type>videos|reviews|full-episodes)/(?P<id>.*?)/(?P<title>.*)'
    _TEST = {
        u'url': u'http://www.gametrailers.com/videos/zbvr8i/mirror-s-edge-2-e3-2013--debut-trailer',
        u'file': u'70e9a5d7-cf25-4a10-9104-6f3e7342ae0d.flv',
        u'md5': u'c3edbc995ab4081976e16779bd96a878',
        u'info_dict': {
            u"title": u"E3 2013: Debut Trailer"
        },
        u'skip': u'Requires rtmpdump'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        mgid = self._search_regex([r'data-video="(?P<mgid>mgid:.*?)"',
                                   r'data-contentId=\'(?P<mgid>mgid:.*?)\''],
                                  webpage, u'mgid')

        data = compat_urllib_parse.urlencode({'uri': mgid, 'acceptMethods': 'fms'})
        info_page = self._download_webpage('http://www.gametrailers.com/feeds/mrss?' + data,
                                           video_id, u'Downloading video info')
        doc = xml.etree.ElementTree.fromstring(info_page.encode('utf-8'))
        default_thumb = doc.find('./channel/image/url').text

        media_namespace = {'media': 'http://search.yahoo.com/mrss/'}
        parts = [{
            'title': video_doc.find('title').text,
            'ext': 'flv',
            'id': video_doc.find('guid').text.rpartition(':')[2],
            # Videos are actually flv not mp4
            'url': self._get_video_url(video_doc.find('media:group/media:content', media_namespace).attrib['url'], video_id),
            # The thumbnail may not be defined, it would be ''
            'thumbnail': video_doc.find('media:group/media:thumbnail', media_namespace).attrib['url'] or default_thumb,
            'description': video_doc.find('description').text,
        } for video_doc in doc.findall('./channel/item')]
        return parts

    def _get_video_url(self, mediagen_url, video_id):
        if 'acceptMethods' not in mediagen_url:
            mediagen_url += '&acceptMethods=fms'
        links_webpage = self._download_webpage(mediagen_url,
                                               video_id, u'Downloading video urls info')
        doc = xml.etree.ElementTree.fromstring(links_webpage)
        urls = list(doc.iter('src'))
        if len(urls) == 0:
            raise ExtractorError(u'Unable to extract video url')
        # They are sorted from worst to best quality
        return urls[-1].text

