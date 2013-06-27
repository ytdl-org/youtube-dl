import re
import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)

class VevoIE(InfoExtractor):
    """
    Accecps urls from vevo.com or in the format 'vevo:{id}'
    (currently used by MTVIE)
    """
    _VALID_URL = r'((http://www.vevo.com/watch/.*?/.*?/)|(vevo:))(?P<id>.*)$'
    _TEST = {
        u'url': u'http://www.vevo.com/watch/hurts/somebody-to-die-for/GB1101300280',
        u'file': u'GB1101300280.mp4',
        u'md5': u'06bea460acb744eab74a9d7dcb4bfd61',
        u'info_dict': {
            u"upload_date": u"20130624", 
            u"uploader": u"Hurts", 
            u"title": u"Somebody To Die For"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        json_url = 'http://www.vevo.com/data/video/%s' % video_id
        base_url = 'http://smil.lvl3.vevo.com'
        videos_url = '%s/Video/V2/VFILE/%s/%sr.smil' % (base_url, video_id, video_id.lower())
        info_json = self._download_webpage(json_url, video_id, u'Downloading json info')
        links_webpage = self._download_webpage(videos_url, video_id, u'Downloading videos urls')

        self.report_extraction(video_id)
        video_info = json.loads(info_json)
        m_urls = list(re.finditer(r'<video src="(?P<ext>.*?):(?P<url>.*?)"', links_webpage))
        if m_urls is None or len(m_urls) == 0:
            raise ExtractorError(u'Unable to extract video url')
        # They are sorted from worst to best quality
        m_url = m_urls[-1]
        video_url = base_url + m_url.group('url')
        ext = m_url.group('ext')

        return {'url': video_url,
                'ext': ext,
                'id': video_id,
                'title': video_info['title'],
                'thumbnail': video_info['img'],
                'upload_date': video_info['launchDate'].replace('/',''),
                'uploader': video_info['Artists'][0]['title'],
                }
