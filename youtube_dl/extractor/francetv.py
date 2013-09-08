# encoding: utf-8
import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
)


class PluzzIE(InfoExtractor):
    IE_NAME = u'pluzz.francetv.fr'
    _VALID_URL = r'https?://pluzz\.francetv\.fr/videos/(.*?)\.html'

    _TEST = {
        u'url': u'http://pluzz.francetv.fr/videos/allo_rufo_saison5_,88439064.html',
        u'file': u'88439064.mp4',
        u'info_dict': {
            u'title': u'Allô Rufo',
            u'description': u'md5:d909f1ebdf963814b65772aea250400e',
        },
        u'params': {
            u'skip_download': True,
        },
    }

    def _real_extract(self, url):
        title = re.match(self._VALID_URL, url).group(1)
        webpage = self._download_webpage(url, title)
        video_id = self._search_regex(
            r'data-diffusion="(\d+)"', webpage, 'ID')

        xml_desc = self._download_webpage(
            'http://www.pluzz.fr/appftv/webservices/video/'
            'getInfosOeuvre.php?id-diffusion='
            + video_id, title, 'Downloading XML config')
        info = xml.etree.ElementTree.fromstring(xml_desc.encode('utf-8'))

        manifest_url = info.find('videos/video/url').text
        video_url = manifest_url.replace('manifest.f4m', 'index_2_av.m3u8')
        video_url = video_url.replace('/z/', '/i/')
        thumbnail_path = info.find('image').text

        return {'id': video_id,
                'ext': 'mp4',
                'url': video_url,
                'title': info.find('titre').text,
                'thumbnail': compat_urlparse.urljoin(url, thumbnail_path),
                'description': info.find('synopsis').text,
                }
