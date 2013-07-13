import re

from .common import InfoExtractor

class InstagramIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?instagram.com/p/(.*?)/'
    _TEST = {
        u'url': u'http://instagram.com/p/aye83DjauH/?foo=bar#abc',
        u'file': u'aye83DjauH.mp4',
        u'md5': u'0d2da106a9d2631273e192b372806516',
        u'info_dict': {
            u"uploader_id": u"naomipq", 
            u"title": u"Video by naomipq"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        webpage = self._download_webpage(url, video_id)
        html_title = self._html_search_regex(
            r'<title>(.+?)</title>',
            webpage, u'title', flags=re.DOTALL)
        title = re.sub(u'(?: *\(Videos?\))? \u2022 Instagram$', '', html_title).strip()
        uploader_id = self._html_search_regex(
            r'<div class="media-user" id="media_user">.*?<h2><a href="[^"]*">([^<]*)</a></h2>',
            webpage, u'uploader id', fatal=False, flags=re.DOTALL)
        ext = 'mp4'

        return [{
            'id':        video_id,
            'url':       self._og_search_video_url(webpage),
            'ext':       ext,
            'title':     title,
            'thumbnail': self._og_search_thumbnail(webpage),
            'uploader_id' : uploader_id
        }]
