import re
from ..utils import compat_urllib_parse
from .common import InfoExtractor


class EhowIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?ehow\.com/([^/]+)'
    _TEST = {
        u'url': u'http://www.ehow.com/video_12245069_hardwood-flooring-basics.html',
        u'file': u'12245069.flv',
        u'md5': u'9809b4e3f115ae2088440bcb4efbf371',
        u'info_dict': {
            u"title": u"Hardwood Flooring Basics",
            u"description": u"Hardwood flooring may be time consuming, but its ultimately a pretty straightforward concept. Learn about hardwood flooring basics with help from a hardware flooring business owner in this free video...",
   			u"uploader": u"Erick Nathan"
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

