import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import unified_strdate

class CanalplusIE(InfoExtractor):
    _VALID_URL = r'https?://(www\.canalplus\.fr/.*?\?vid=|player\.canalplus\.fr/#/)(?P<id>\d+)'
    _VIDEO_INFO_TEMPLATE = 'http://service.canal-plus.com/video/rest/getVideosLiees/cplus/%s'
    IE_NAME = u'canalplus.fr'

    _TEST = {
        u'url': u'http://www.canalplus.fr/c-divertissement/pid3351-c-le-petit-journal.html?vid=889861',
        u'file': u'889861.flv',
        u'md5': u'590a888158b5f0d6832f84001fbf3e99',
        u'info_dict': {
            u'title': u'Le Petit Journal 20/06/13 - La guerre des drone',
            u'upload_date': u'20130620',
        },
        u'skip': u'Requires rtmpdump'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        info_url = self._VIDEO_INFO_TEMPLATE % video_id
        info_page = self._download_webpage(info_url,video_id, 
                                           u'Downloading video info')

        self.report_extraction(video_id)
        doc = xml.etree.ElementTree.fromstring(info_page.encode('utf-8'))
        video_info = [video for video in doc if video.find('ID').text == video_id][0]
        infos = video_info.find('INFOS')
        media = video_info.find('MEDIA')
        formats = [media.find('VIDEOS/%s' % format)
            for format in ['BAS_DEBIT', 'HAUT_DEBIT', 'HD']]
        video_url = [format.text for format in formats if format is not None][-1]

        return {'id': video_id,
                'title': u'%s - %s' % (infos.find('TITRAGE/TITRE').text,
                                       infos.find('TITRAGE/SOUS_TITRE').text),
                'url': video_url,
                'ext': 'flv',
                'upload_date': unified_strdate(infos.find('PUBLICATION/DATE').text),
                'thumbnail': media.find('IMAGES/GRAND').text,
                }
