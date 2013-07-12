import re

from .common import InfoExtractor

class StatigramIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?statigr\.am/p/([^/]+)'
    _TEST = {
        u'url': u'http://statigr.am/p/484091715184808010_284179915',
        u'file': u'484091715184808010_284179915.mp4',
        u'md5': u'deda4ff333abe2e118740321e992605b',
        u'info_dict': {
            u"uploader_id": u"videoseconds", 
            u"title": u"Instagram photo by @videoseconds"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        webpage = self._download_webpage(url, video_id)
        html_title = self._html_search_regex(
            r'<title>(.+?)</title>',
            webpage, u'title')
        title = re.sub(r'(?: *\(Videos?\))? \| Statigram$', '', html_title)
        uploader_id = self._html_search_regex(
            r'@([^ ]+)', title, u'uploader name', fatal=False)
        ext = 'mp4'

        return [{
            'id':        video_id,
            'url':       self._og_search_video_url(webpage),
            'ext':       ext,
            'title':     title,
            'thumbnail': self._og_search_thumbnail(webpage),
            'uploader_id' : uploader_id
        }]
