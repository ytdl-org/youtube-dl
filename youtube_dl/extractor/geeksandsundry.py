from .common import InfoExtractor

import re


class GeeksAndSundryIE(InfoExtractor):
    _VALID_URL = r'https://(?:\w+\.)geekandsundry.com/(?P<title>.+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page = mobj.group('title')
        webpage_url = "https://geekandsundry.com/" + page
        webpage = self._download_webpage(webpage_url, page)

        self.report_extraction(page)
        
        video_id = self._html_search_regex(r'data-video-id=\"(\d+)\"', webpage, u'video id')
        pub_id = self._html_search_regex(r'data-account=\"(\d+)\"', webpage, u'pub id')

        video_url = "http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=%s" % (video_id, pub_id)

        return [{
            'id':        page,
            'url':       video_url,
            'ext':       'mp4',
            'title':     self._og_search_title(webpage),
        }]

    _TEST = {
        u'url': u'https://geekandsundry.com/titansgrave-chapter-0/',
        u'md5': u'd3507646e87ffb717b8a328b3bb824a8',
        u'info_dict': {
            u"id": u"titansgrave-chapter-0/",
            u"ext": u"mp4",
            u"title": u"Titansgrave - Chapter 0 _ Geek and Sundry-titansgrave-chapter-0"
        }
    }
