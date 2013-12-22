import re
import base64

from .common import InfoExtractor


class WimpIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?wimp\.com/([^/]+)/'
    _TEST = {
        u'url': u'http://www.wimp.com/deerfence/',
        u'file': u'deerfence.flv',
        u'md5': u'8b215e2e0168c6081a1cf84b2846a2b5',
        u'info_dict': {
            u"title": u"Watch Till End: Herd of deer jump over a fence.",
            u"description": u"These deer look as fluid as running water when they jump over this fence as a herd. This video is one that needs to be watched until the very end for the true majesty to be witnessed, but once it comes, it's sure to take your breath away.",
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        webpage = self._download_webpage(url, video_id)
        googleString = self._search_regex("googleCode = '(.*?)'", webpage, 'file url')
        googleString = base64.b64decode(googleString).decode('ascii')
        final_url = self._search_regex('","(.*?)"', googleString, u'final video url')

        return {
            'id': video_id,
            'url': final_url,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
        }
