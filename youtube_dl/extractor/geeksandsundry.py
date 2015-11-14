from __future__ import unicode_literals

from .common import InfoExtractor
import re


class GeeksAndSundryIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?geekandsundry\.com/(?P<title>.+)'
    _TEST = {
        'url': 'http://www.geekandsundry.com/tabletop-bonus-wils-final-thoughts-on-dread/',
        'md5': '02206df2e7a1805349a75af8df396222',
        'info_dict': {
            'id': 'tabletop-bonus-wils-final-thoughts-on-dread/',
            'ext': 'mp4',
            'title': 'TableTop Bonus! Wil\u2019s Final Thoughts on Dread | Geek and Sundry',
        }
    }


    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page = mobj.group('title')
        webpage_url = "https://geekandsundry.com/" + page
        webpage = self._download_webpage(webpage_url, page)

        self.report_extraction(page)

        video_id = self._html_search_regex(r'data-video-id=\"(\d+)\"', webpage, u'video id')
        pub_id = self._html_search_regex(r'data-account=\"(\d+)\"', webpage, u'pub id')

        video_url = "http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=%s" % (video_id, pub_id)

        return {
            'id': page,
            'url': video_url,
            'ext': 'mp4',
            'title': self._og_search_title(webpage),
        }
