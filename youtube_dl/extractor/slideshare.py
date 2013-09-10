import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    ExtractorError,
)


class SlideshareIE(InfoExtractor):
    _VALID_URL = r'https?://www\.slideshare\.net/[^/]+?/(?P<title>.+?)($|\?)'

    _TEST = {
        u'url': u'http://www.slideshare.net/Dataversity/keynote-presentation-managing-scale-and-complexity',
        u'file': u'25665706.mp4',
        u'info_dict': {
            u'title': u'Managing Scale and Complexity',
            u'description': u'This was a keynote presentation at the NoSQL Now! 2013 Conference & Expo (http://www.nosqlnow.com). This presentation was given by Adrian Cockcroft from Netflix',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_title = mobj.group('title')
        webpage = self._download_webpage(url, page_title)
        slideshare_obj = self._search_regex(
            r'var slideshare_object =  ({.*?}); var user_info =',
            webpage, u'slideshare object')
        info = json.loads(slideshare_obj)
        if info['slideshow']['type'] != u'video':
            raise ExtractorError(u'Webpage type is "%s": only video extraction is supported for Slideshare' % info['slideshow']['type'], expected=True)

        doc = info['doc']
        bucket = info['jsplayer']['video_bucket']
        ext = info['jsplayer']['video_extension']
        video_url = compat_urlparse.urljoin(bucket, doc + '-SD.' + ext)

        return {
            '_type': 'video',
            'id': info['slideshow']['id'],
            'title': info['slideshow']['title'],
            'ext': ext,
            'url': video_url,
            'thumbnail': info['slideshow']['pin_image_url'],
            'description': self._og_search_description(webpage),
        }
