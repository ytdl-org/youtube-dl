from .common import InfoExtractor
from math import ceil
import re

class ToypicsIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?videos\.toypics\.net/.*'
    _TEST = {
        'url': 'http://videos.toypics.net/view/514/chancebulged,-2-1/',
        #'md5': '8a8b546956bbd0e769dbe28f6e80abb3', == $head -c10K 12929646011616163504.mp4 |md5sum //no idea why it fails
        'info_dict': {
            'id': '514',
            'ext': 'mp4',
            'title': 'Chance-Bulge\'d, 2',
            'age_limit': 18
        }
    }
    PAGINATED=8

    def _real_extract(self, url):
        mobj = re.match(r'(http://)?videos\.toypics\.net/(?P<username>[^/?]+)$', url)
        if not mobj:
            return self.extract_one(url)
        return [self.extract_one(u) for u in self.process_paginated(url,
            r'public/">Public Videos \((?P<videos_count>[0-9]+)\)</a></li>',
            r'<p class="video-entry-title">\n\s*<a href="(http://videos.toypics.net/view/[^"]+)">'
        )]

    def process_paginated(self, profile_url, re_total, re_video_page):
        profile_page = self._download_webpage(profile_url, 'profile' , 'getting profile page: '+profile_url)
        videos_count = self._html_search_regex(re_total, profile_page, 'videos count')
        lst = []
        for n in xrange(1,int(ceil(float(videos_count)/self.PAGINATED)) +1):
            lpage_url = profile_url +'/public/%d'%n
            lpage = self._download_webpage(lpage_url, 'page %d'%n)
            lst.extend(re.findall(re_video_page, lpage))
        return lst

    def extract_one(self,url):
        mobj = re.match(r'(http://)?videos\.toypics\.net/view/(?P<videoid>[0-9]+)/.*', url)
        video_id = mobj.group('videoid')
        page = self._download_webpage(url, video_id, 'getting page: '+url)
        video_url = self._html_search_regex(
            r'src:\s+"(http://static[0-9]+\.toypics\.net/flvideo/[^"]+)"', page, 'video URL')
        title = self._html_search_regex(
            r'<title>Toypics - ([^<]+)</title>', page, 'title')
        username = self._html_search_regex(
            r'toypics.net/([^/"]+)" class="user-name">', page, 'username')
        return {
            'id': video_id,
            'url': video_url,
            'ext': video_url[-3:],
            'title': title,
            'uploader': username,
            'age_limit': 18
        }
