import re

from .common import InfoExtractor
from ..utils import determine_ext

class FreesoundIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?freesound\.org/people/([^/]+)/sounds/(?P<id>[^/]+)'
    _TEST = {
        u'url': u'http://www.freesound.org/people/miklovan/sounds/194503/',
        u'file': u'194503.mp3',
        u'md5': u'12280ceb42c81f19a515c745eae07650',
        u'info_dict': {
            u"title": u"gulls in the city.wav",
            u"uploader" : u"miklovan",
            u'description': u'the sounds of seagulls in the city',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        music_id = mobj.group('id')
        webpage = self._download_webpage(url, music_id)
        title = self._html_search_regex(r'<div id="single_sample_header">.*?<a href="#">(.+?)</a>',
                                webpage, 'music title', flags=re.DOTALL)
        music_url = self._og_search_property('audio', webpage, 'music url')
        description = self._html_search_regex(r'<div id="sound_description">(.*?)</div>',
                                webpage, 'description', fatal=False, flags=re.DOTALL)

        return [{
            'id':       music_id,
            'title':    title,            
            'url':      music_url,
            'uploader': self._og_search_property('audio:artist', webpage, 'music uploader'),
            'ext':      determine_ext(music_url),
            'description': description,
        }]
