import re

from .common import InfoExtractor
from ..utils import determine_ext


class KankanIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.*?\.)?kankan\.com/.+?/(?P<id>\d+)\.shtml'
    
    _TEST = {
        u'url': u'http://yinyue.kankan.com/vod/48/48863.shtml',
        u'file': u'48863.flv',
        u'md5': u'29aca1e47ae68fc28804aca89f29507e',
        u'info_dict': {
            u'title': u'Ready To Go',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        title = self._search_regex(r'G_TITLE=[\'"](.+?)[\'"]', webpage, u'video title')
        gcid = self._search_regex(r'lurl:[\'"]http://.+?/.+?/(.+?)/', webpage, u'gcid')

        video_info_page = self._download_webpage('http://p2s.cl.kankan.com/getCdnresource_flv?gcid=%s' % gcid,
                                                 video_id, u'Downloading video url info')
        ip = self._search_regex(r'ip:"(.+?)"', video_info_page, u'video url ip')
        path = self._search_regex(r'path:"(.+?)"', video_info_page, u'video url path')
        video_url = 'http://%s%s' % (ip, path)

        return {'id': video_id,
                'title': title,
                'url': video_url,
                'ext': determine_ext(video_url),
                }
