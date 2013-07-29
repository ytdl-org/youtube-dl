import re
import json

from .common import InfoExtractor
from ..utils import determine_ext


class BreakIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?break\.com/video/([^/]+)'
    _TEST = {
        u'url': u'http://www.break.com/video/when-girls-act-like-guys-2468056',
        u'file': u'2468056.mp4',
        u'md5': u'a3513fb1547fba4fb6cfac1bffc6c46b',
        u'info_dict': {
            u"title": u"When Girls Act Like D-Bags"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1).split("-")[-1]
        embed_url = 'http://www.break.com/embed/%s' % video_id
        webpage = self._download_webpage(embed_url, video_id)
        info_json = self._search_regex(r'var embedVars = ({.*?});', webpage,
                                       u'info json', flags=re.DOTALL)
        info = json.loads(info_json)
        video_url = info['videoUri']
        m_youtube = re.search(r'(https?://www\.youtube\.com/watch\?v=.*)', video_url)
        if m_youtube is not None:
            return self.url_result(m_youtube.group(1), 'Youtube')
        final_url = video_url + '?' + info['AuthToken']
        return [{
            'id':        video_id,
            'url':       final_url,
            'ext':       determine_ext(final_url),
            'title':     info['contentName'],
            'thumbnail': info['thumbUri'],
        }]
