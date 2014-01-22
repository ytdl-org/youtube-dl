# encoding: utf-8
import re

from .common import InfoExtractor
from ..utils import unified_strdate


class CanalplusIE(InfoExtractor):
    _VALID_URL = r'https?://(www\.canalplus\.fr/.*?/(?P<path>.*)|player\.canalplus\.fr/#/(?P<id>\d+))'
    _VIDEO_INFO_TEMPLATE = 'http://service.canal-plus.com/video/rest/getVideosLiees/cplus/%s'
    IE_NAME = u'canalplus.fr'

    _TEST = {
        u'url': u'http://www.canalplus.fr/c-infos-documentaires/pid1830-c-zapping.html?vid=922470',
        u'file': u'922470.flv',
        u'info_dict': {
            u'title': u'Zapping - 26/08/13',
            u'description': u'Le meilleur de toutes les chaînes, tous les jours.\nEmission du 26 août 2013',
            u'upload_date': u'20130826',
        },
        u'params': {
            u'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.groupdict().get('id')
        if video_id is None:
            webpage = self._download_webpage(url, mobj.group('path'))
            video_id = self._search_regex(r'videoId = "(\d+)";', webpage, u'video id')
        info_url = self._VIDEO_INFO_TEMPLATE % video_id
        doc = self._download_xml(info_url,video_id, 
                                           u'Downloading video info')

        self.report_extraction(video_id)
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
                'description': infos.find('DESCRIPTION').text,
                'view_count': int(infos.find('NB_VUES').text),
                }
