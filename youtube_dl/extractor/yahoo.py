import datetime
import itertools
import json
import re

from .common import InfoExtractor, SearchInfoExtractor
from ..utils import (
    compat_urllib_parse,

    ExtractorError,
)

class YahooIE(InfoExtractor):
    IE_DESC = u'Yahoo screen'
    _VALID_URL = r'http://screen\.yahoo\.com/.*?-(?P<id>\d*?)\.html'
    _TEST = {
        u'url': u'http://screen.yahoo.com/julian-smith-travis-legg-watch-214727115.html',
        u'file': u'214727115.flv',
        u'md5': u'2e717f169c1be93d84d3794a00d4a325',
        u'info_dict': {
            u"title": u"Julian Smith & Travis Legg Watch Julian Smith"
        },
        u'skip': u'Requires rtmpdump'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        m_id = re.search(r'YUI\.namespace\("Media"\)\.CONTENT_ID = "(?P<new_id>.+?)";', webpage)

        if m_id is None: 
            # TODO: Check which url parameters are required
            info_url = 'http://cosmos.bcst.yahoo.com/rest/v2/pops;lmsoverride=1;outputformat=mrss;cb=974419660;id=%s;rd=news.yahoo.com;datacontext=mdb;lg=KCa2IihxG3qE60vQ7HtyUy' % video_id
            webpage = self._download_webpage(info_url, video_id, u'Downloading info webpage')
            info_re = r'''<title><!\[CDATA\[(?P<title>.*?)\]\]></title>.*
                        <description><!\[CDATA\[(?P<description>.*?)\]\]></description>.*
                        <media:pubStart><!\[CDATA\[(?P<date>.*?)\ .*\]\]></media:pubStart>.*
                        <media:content\ medium="image"\ url="(?P<thumb>.*?)"\ name="LARGETHUMB"
                        '''
            self.report_extraction(video_id)
            m_info = re.search(info_re, webpage, re.VERBOSE|re.DOTALL)
            if m_info is None:
                raise ExtractorError(u'Unable to extract video info')
            video_title = m_info.group('title')
            video_description = m_info.group('description')
            video_thumb = m_info.group('thumb')
            video_date = m_info.group('date')
            video_date = datetime.datetime.strptime(video_date, '%m/%d/%Y').strftime('%Y%m%d')
    
            # TODO: Find a way to get mp4 videos
            rest_url = 'http://cosmos.bcst.yahoo.com/rest/v2/pops;element=stream;outputformat=mrss;id=%s;lmsoverride=1;bw=375;dynamicstream=1;cb=83521105;tech=flv,mp4;rd=news.yahoo.com;datacontext=mdb;lg=KCa2IihxG3qE60vQ7HtyUy' % video_id
            webpage = self._download_webpage(rest_url, video_id, u'Downloading video url webpage')
            m_rest = re.search(r'<media:content url="(?P<url>.*?)" path="(?P<path>.*?)"', webpage)
            video_url = m_rest.group('url')
            video_path = m_rest.group('path')
            if m_rest is None:
                raise ExtractorError(u'Unable to extract video url')

        else: # We have to use a different method if another id is defined
            long_id = m_id.group('new_id')
            info_url = 'http://video.query.yahoo.com/v1/public/yql?q=SELECT%20*%20FROM%20yahoo.media.video.streams%20WHERE%20id%3D%22' + long_id + '%22%20AND%20format%3D%22mp4%2Cflv%22%20AND%20protocol%3D%22rtmp%2Chttp%22%20AND%20plrs%3D%2286Gj0vCaSzV_Iuf6hNylf2%22%20AND%20acctid%3D%22389%22%20AND%20plidl%3D%22%22%20AND%20pspid%3D%22792700001%22%20AND%20offnetwork%3D%22false%22%20AND%20site%3D%22ivy%22%20AND%20lang%3D%22en-US%22%20AND%20region%3D%22US%22%20AND%20override%3D%22none%22%3B&env=prod&format=json&callback=YUI.Env.JSONP.yui_3_8_1_1_1368368376830_335'
            webpage = self._download_webpage(info_url, video_id, u'Downloading info json')
            json_str = re.search(r'YUI.Env.JSONP.yui.*?\((.*?)\);', webpage).group(1)
            info = json.loads(json_str)
            res = info[u'query'][u'results'][u'mediaObj'][0]
            stream = res[u'streams'][0]
            video_path = stream[u'path']
            video_url = stream[u'host']
            meta = res[u'meta']
            video_title = meta[u'title']
            video_description = meta[u'description']
            video_thumb = meta[u'thumbnail']
            video_date = None # I can't find it

        info_dict = {
                     'id': video_id,
                     'url': video_url,
                     'play_path': video_path,
                     'title':video_title,
                     'description': video_description,
                     'thumbnail': video_thumb,
                     'upload_date': video_date,
                     'ext': 'flv',
                     }
        return info_dict

class YahooSearchIE(SearchInfoExtractor):
    IE_DESC = u'Yahoo screen search'
    _MAX_RESULTS = 1000
    IE_NAME = u'screen.yahoo:search'
    _SEARCH_KEY = 'yvsearch'

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""

        res = {
            '_type': 'playlist',
            'id': query,
            'entries': []
        }
        for pagenum in itertools.count(0): 
            result_url = u'http://video.search.yahoo.com/search/?p=%s&fr=screen&o=js&gs=0&b=%d' % (compat_urllib_parse.quote_plus(query), pagenum * 30)
            webpage = self._download_webpage(result_url, query,
                                             note='Downloading results page '+str(pagenum+1))
            info = json.loads(webpage)
            m = info[u'm']
            results = info[u'results']

            for (i, r) in enumerate(results):
                if (pagenum * 30) +i >= n:
                    break
                mobj = re.search(r'(?P<url>screen\.yahoo\.com/.*?-\d*?\.html)"', r)
                e = self.url_result('http://' + mobj.group('url'), 'Yahoo')
                res['entries'].append(e)
            if (pagenum * 30 +i >= n) or (m[u'last'] >= (m[u'total'] -1 )):
                break

        return res
