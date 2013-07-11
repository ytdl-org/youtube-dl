import re
from ..utils import compat_urllib_parse
from .common import InfoExtractor


class EhowIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?ehow\.com/([^/]+)'
    _TEST = {
        u'url': u'http://www.break.com/video/when-girls-act-like-guys-2468056',
        u'file': u'2468056.mp4',
        u'md5': u'a3513fb1547fba4fb6cfac1bffc6c46b',
        u'info_dict': {
            u"title": u"When Girls Act Like D-Bags"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1).split("_")[1]
        webpage = self._download_webpage(url, video_id)
        video_url = self._search_regex(r'[^A-Za-z0-9]?(?:file|source)=(http[^\'"&]*)',
            webpage, u'video URL')
        final_url = compat_urllib_parse.unquote(video_url)        
        thumbnail_url = self._search_regex(r'<meta property="og:image" content="(.+?)" />',
            webpage, u'thumbnail URL')
        uploader = self._search_regex(r'<meta name="uploader" content="(.+?)" />',
            webpage, u'uploader')
        title = self._search_regex(r'<meta property="og:title" content="(.+?)" />',
            webpage, u'Video title').replace(' | eHow','')
        description = self._search_regex(r'<meta property="og:description" content="(.+?)" />',
            webpage, u'video description')
        ext = final_url.split('.')[-1]
        return [{
            'id':          video_id,
            'url':         final_url,
            'ext':         ext,
            'title':       title,
            'thumbnail':   thumbnail_url,
            'description': description,
            'uploader':    uploader,
        }]

