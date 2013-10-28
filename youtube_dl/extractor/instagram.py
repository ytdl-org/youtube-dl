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
            u"title": u"Video by naomipq",
            u'description': u'md5:1f17f0ab29bd6fe2bfad705f58de3cb8',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        webpage = self._download_webpage(url, video_id)
        uploader_id = self._search_regex(r'"owner":{"username":"(.+?)"',
            webpage, u'uploader id', fatal=False)
        desc = self._search_regex(r'"caption":"(.*?)"', webpage, u'description',
            fatal=False)

        return [{
            'id':        video_id,
            'url':       self._og_search_video_url(webpage, secure=False),
            'ext':       'mp4',
            'title':     u'Video by %s' % uploader_id,
            'thumbnail': self._og_search_thumbnail(webpage),
            'uploader_id' : uploader_id,
            'description': desc,
        }]
