# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import datetime
import time
import urllib.request
import json


class AudiomackIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?audiomack\.com/song/(?P<id>[\w/-]+)'
    _TEST = {
        'url': 'https://www.audiomack.com/song/crewneckkramer/story-i-tell',
        'info_dict': {
            'id': 'story-i-tell',
            'ext': 'mp3',
            'title': 'story-i-tell'
        }
    }

    def _real_extract(self, url):
        # TODO more code goes here, for example ...
        #webpage = self._download_webpage(url, video_id)
        #title = self._html_search_regex(r'<h1>(.*?)</h1>', webpage, 'title')
	
        assert("/song/" in url)
        songurl = url[url.index("/song/")+5:]
        title = songurl[songurl.rindex("/")+1:]
        video_id = title
        t = int(time.mktime(datetime.datetime.now().timetuple()))
        s = "http://www.audiomack.com/api/music/url/song"+songurl+"?_="+str(t)
        f = urllib.request.urlopen(s)
        j = f.read(1000).decode("utf-8")
        data = json.loads(j)

        return {
            'id': video_id,
            'title': title,
            'url' : data["url"],
            'ext' : 'mp3'
            # TODO more properties (see youtube_dl/extractor/common.py)
        }   
