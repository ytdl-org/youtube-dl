import re
import json
import time

from .common import InfoExtractor


class ExfmIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?ex\.fm/song/([^/]+)'
    _SOUNDCLOUD_URL_ = r'(?:http://)?(?:www\.)?api\.soundcloud.com/tracks/([^/]+)/stream'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        info_url = "http://ex.fm/api/v3/song/%s" %(video_id)
        webpage = self._download_webpage(info_url, video_id)
        info = json.loads(webpage)
        song_url = re.match(self._SOUNDCLOUD_URL_,info['song']['url'])
        if song_url is not None:
        	song_url = song_url.group() + "?client_id=b45b1aa10f1ac2941910a7f0d10f8e28"
        else:
        	song_url = info['song']['url']
        return [{
            'id':          video_id,
            'url':         song_url,
            'ext':         'mp3',
            'title':       info['song']['title'],
            'thumbnail':   info['song']['image']['large'],
            'uploader':    info['song']['artist'],
            'view_count':  info['song']['loved_count'],
        }]
