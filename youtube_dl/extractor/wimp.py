import re
import base64
from .common import InfoExtractor


class WimpIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?wimp\.com/([^/]+)/'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        webpage = self._download_webpage(url, video_id)
        title = re.search('\<meta name\="description" content="(.+?)" \/\>',webpage).group(1)
        thumbnail_url = re.search('\<meta property\=\"og\:image" content\=\"(.+?)\" />',webpage).group(1)
        googleString = re.search("googleCode = '(.*?)'", webpage)
        googleString = base64.b64decode(googleString.group(1))
        final_url = re.search('","(.*?)"', googleString).group(1)
        ext = final_url.split('.')[-1]
        return [{
            'id':        video_id,
            'url':       final_url,
            'ext':       ext,
            'title':     title,
            'thumbnail': thumbnail_url,
        }]
