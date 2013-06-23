import re

from .common import InfoExtractor


class BreakIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?break\.com/video/([^/]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1).split("-")[-1]
        webpage = self._download_webpage(url, video_id)
        video_url = re.search(r"videoPath: '(.+?)',",webpage).group(1)
        key = re.search(r"icon: '(.+?)',",webpage).group(1)
        final_url = str(video_url)+"?"+str(key)
        thumbnail_url = re.search(r"thumbnailURL: '(.+?)'",webpage).group(1)
        title = re.search(r"sVidTitle: '(.+)',",webpage).group(1)
        ext = video_url.split('.')[-1]
        return [{
            'id':        video_id,
            'url':       final_url,
            'ext':       ext,
            'title':     title,
            'thumbnail': thumbnail_url,
        }]
