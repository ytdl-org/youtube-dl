import json
import re

from .common import InfoExtractor
from ..utils import determine_ext


class NewgroundsIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?newgrounds\.com/audio/listen/(?P<id>\d+)'
    _TEST = {
        u'url': u'http://www.newgrounds.com/audio/listen/549479',
        u'file': u'549479.mp3',
        u'md5': u'fe6033d297591288fa1c1f780386f07a',
        u'info_dict': {
            u"title": u"B7 - BusMode",
            u"uploader": u"Burn7",
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        music_id = mobj.group('id')
        webpage = self._download_webpage(url, music_id)
        
        title = self._html_search_regex(r',"name":"([^"]+)",', webpage, u'music title')
        uploader = self._html_search_regex(r',"artist":"([^"]+)",', webpage, u'music uploader')
        
        music_url_json_string = self._html_search_regex(r'({"url":"[^"]+"),', webpage, u'music url') + '}'
        music_url_json = json.loads(music_url_json_string)
        music_url = music_url_json['url']

        return {
            'id':       music_id,
            'title':    title,
            'url':      music_url,
            'uploader': uploader,
            'ext':      determine_ext(music_url),
        }
