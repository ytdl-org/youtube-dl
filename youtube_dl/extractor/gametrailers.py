import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,

    ExtractorError,
)

class GametrailersIE(InfoExtractor):
    _VALID_URL = r'http://www.gametrailers.com/(?P<type>videos|reviews|full-episodes)/(?P<id>.*?)/(?P<title>.*)'
    _TEST = {
        u'url': u'http://www.gametrailers.com/videos/zbvr8i/mirror-s-edge-2-e3-2013--debut-trailer',
        u'file': u'zbvr8i.flv',
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
        video_type = mobj.group('type')
        webpage = self._download_webpage(url, video_id)
        if video_type == 'full-episodes':
            mgid_re = r'data-video="(?P<mgid>mgid:.*?)"'
        else:
            mgid_re = r'data-contentId=\'(?P<mgid>mgid:.*?)\''
        mgid = self._search_regex(mgid_re, webpage, u'mgid')
        data = compat_urllib_parse.urlencode({'uri': mgid, 'acceptMethods': 'fms'})

        info_page = self._download_webpage('http://www.gametrailers.com/feeds/mrss?' + data,
                                           video_id, u'Downloading video info')
        links_webpage = self._download_webpage('http://www.gametrailers.com/feeds/mediagen/?' + data,
                                               video_id, u'Downloading video urls info')

        self.report_extraction(video_id)
        info_re = r'''<title><!\[CDATA\[(?P<title>.*?)\]\]></title>.*
                      <description><!\[CDATA\[(?P<description>.*?)\]\]></description>.*
                      <image>.*
                        <url>(?P<thumb>.*?)</url>.*
                      </image>'''

        m_info = re.search(info_re, info_page, re.VERBOSE|re.DOTALL)
        if m_info is None:
            raise ExtractorError(u'Unable to extract video info')
        video_title = m_info.group('title')
        video_description = m_info.group('description')
        video_thumb = m_info.group('thumb')

        m_urls = list(re.finditer(r'<src>(?P<url>.*)</src>', links_webpage))
        if m_urls is None or len(m_urls) == 0:
            raise ExtractorError(u'Unable to extract video url')
        # They are sorted from worst to best quality
        video_url = m_urls[-1].group('url')

        return {'url':         video_url,
                'id':          video_id,
                'title':       video_title,
                # Videos are actually flv not mp4
                'ext':         'flv',
                'thumbnail':   video_thumb,
                'description': video_description,
                }
