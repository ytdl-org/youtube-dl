import re

from ..utils import (
    compat_urllib_parse,
    determine_ext
)
from .common import InfoExtractor


class EHowIE(InfoExtractor):
    IE_NAME = u'eHow'
    _VALID_URL = r'(?:https?://)?(?:www\.)?ehow\.com/[^/_?]*_(?P<id>[0-9]+)'
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
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        video_url = self._search_regex(r'(?:file|source)=(http[^\'"&]*)',
            webpage, u'video URL')
        final_url = compat_urllib_parse.unquote(video_url)        
        uploader = self._search_regex(r'<meta name="uploader" content="(.+?)" />',
            webpage, u'uploader')
        title = self._og_search_title(webpage).replace(' | eHow', '')
        ext = determine_ext(final_url)

        return {
            '_type':       'video',
            'id':          video_id,
            'url':         final_url,
            'ext':         ext,
            'title':       title,
            'thumbnail':   self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
            'uploader':    uploader,
        }

