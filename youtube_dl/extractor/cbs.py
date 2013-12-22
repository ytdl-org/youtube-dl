import re

from .common import InfoExtractor


class CBSIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cbs\.com/shows/[^/]+/video/(?P<id>[^/]+)/.*'

    _TEST = {
        u'url': u'http://www.cbs.com/shows/garth-brooks/video/_u7W953k6la293J7EPTd9oHkSPs6Xn6_/connect-chat-feat-garth-brooks/',
        u'file': u'4JUVEwq3wUT7.flv',
        u'info_dict': {
            u'title': u'Connect Chat feat. Garth Brooks',
            u'description': u'Connect with country music singer Garth Brooks, as he chats with fans on Wednesday November 27, 2013. Be sure to tune in to Garth Brooks: Live from Las Vegas, Friday November 29, at 9/8c on CBS!',
            u'duration': 1495,
        },
        u'params': {
            # rtmp download
            u'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        real_id = self._search_regex(
            r"video\.settings\.pid\s*=\s*'([^']+)';",
            webpage, u'real video ID')
        return self.url_result(u'theplatform:%s' % real_id)
