import re

from .common import InfoExtractor

class StatigramIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?statigr\.am/p/([^/]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        webpage = self._download_webpage(url, video_id)
        video_url = self._html_search_regex(
            r'<meta property="og:video:secure_url" content="(.+?)">',
            webpage, u'video URL')
        thumbnail_url = self._html_search_regex(
            r'<meta property="og:image" content="(.+?)" />',
            webpage, u'thumbnail URL', fatal=False)
        html_title = self._html_search_regex(
            r'<title>(.+?)</title>',
            webpage, u'title')
        title = html_title.rpartition(u' | Statigram')[0]
        uploader_id = self._html_search_regex(
            r'@([^ ]+)', title, u'uploader name', fatal=False)
        ext = 'mp4'

        return [{
            'id':        video_id,
            'url':       video_url,
            'ext':       ext,
            'title':     title,
            'thumbnail': thumbnail_url,
            'uploader_id' : uploader_id
        }]
