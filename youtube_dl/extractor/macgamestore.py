import re

from .common import InfoExtractor
from ..utils import ExtractorError


class MacGameStoreIE(InfoExtractor):
    IE_NAME = u'macgamestore'
    IE_DESC = u'MacGameStore trailers'
    _VALID_URL = r'https?://www\.macgamestore\.com/mediaviewer\.php\?trailer=(?P<id>\d+)'

    _TEST = {
        u'url': u'http://www.macgamestore.com/mediaviewer.php?trailer=2450',
        u'file': u'2450.m4v',
        u'md5': u'8649b8ea684b6666b4c5be736ecddc61',
        u'info_dict': {
            u'title': u'Crow',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        
        webpage = self._download_webpage(url, video_id, u'Downloading trailer page')
        
        if re.search(r'>Missing Media<', webpage) is not None:
            raise ExtractorError(u'Trailer %s does not exist' % video_id, expected=True)
        
        mobj = re.search(r'<title>MacGameStore: (?P<title>.*?) Trailer</title>', webpage)
        video_title = mobj.group('title')
        
        mobj = re.search(r'(?s)<div\s+id="video-player".*?href="(?P<video>[^"]+)"\s*>', webpage)
        video_url = mobj.group('video')
        
        return {
            'id': video_id,
            'url': video_url,
            'title': video_title
        }