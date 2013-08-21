import re

from .common import InfoExtractor

class StatigramIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?statigr\.am/p/([^/]+)'
    _TEST = {
        u'url': u'http://statigr.am/p/522207370455279102_24101272',
        u'file': u'522207370455279102_24101272.mp4',
        u'md5': u'6eb93b882a3ded7c378ee1d6884b1814',
        u'info_dict': {
            u'uploader_id': u'aguynamedpatrick',
            u'title': u'Instagram photo by @aguynamedpatrick (Patrick Janelle)',
        },
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
