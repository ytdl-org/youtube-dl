import re
import json

from .common import InfoExtractor


class ExfmIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?ex\.fm/song/([^/]+)'
    _SOUNDCLOUD_URL_ = r'(?:http://)?(?:www\.)?api\.soundcloud.com/tracks/([^/]+)/stream'
    _TEST = {
        u'url': u'http://ex.fm/song/1bgtzg',
        u'file': u'1bgtzg.mp3',
        u'md5': u'8a7967a3fef10e59a1d6f86240fd41cf',
        u'info_dict': {
            u"title": u"We Can't Stop",
            u"uploader": u"Miley Cyrus",
            u'thumbnail': u'http://i1.sndcdn.com/artworks-000049666230-w9i7ef-t500x500.jpg?9d68d37'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        song_id = mobj.group(1)
        info_url = "http://ex.fm/api/v3/song/%s" %(song_id)
        webpage = self._download_webpage(info_url, song_id)
        info = json.loads(webpage)
        song_url = re.match(self._SOUNDCLOUD_URL_,info['song']['url'])
        if song_url is not None:
        	song_url = song_url.group() + "?client_id=b45b1aa10f1ac2941910a7f0d10f8e28"
        else:
        	song_url = info['song']['url']
        return [{
            'id':          song_id,
            'url':         song_url,
            'ext':         'mp3',
            'title':       info['song']['title'],
            'thumbnail':   info['song']['image']['large'],
            'uploader':    info['song']['artist'],
            'view_count':  info['song']['loved_count'],
        }]
