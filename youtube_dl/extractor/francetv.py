# encoding: utf-8
import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
)


class FranceTVBaseInfoExtractor(InfoExtractor):
    def _extract_video(self, video_id):
        xml_desc = self._download_webpage(
            'http://www.francetvinfo.fr/appftv/webservices/video/'
            'getInfosOeuvre.php?id-diffusion='
            + video_id, video_id, 'Downloading XML config')
        info = xml.etree.ElementTree.fromstring(xml_desc.encode('utf-8'))

        manifest_url = info.find('videos/video/url').text
        video_url = manifest_url.replace('manifest.f4m', 'index_2_av.m3u8')
        video_url = video_url.replace('/z/', '/i/')
        thumbnail_path = info.find('image').text

        return {'id': video_id,
                'ext': 'mp4',
                'url': video_url,
                'title': info.find('titre').text,
                'thumbnail': compat_urlparse.urljoin('http://pluzz.francetv.fr', thumbnail_path),
                'description': info.find('synopsis').text,
                }


class PluzzIE(FranceTVBaseInfoExtractor):
    IE_NAME = u'pluzz.francetv.fr'
    _VALID_URL = r'https?://pluzz\.francetv\.fr/videos/(.*?)\.html'

    # Can't use tests, videos expire in 7 days

    def _real_extract(self, url):
        title = re.match(self._VALID_URL, url).group(1)
        webpage = self._download_webpage(url, title)
        video_id = self._search_regex(
            r'data-diffusion="(\d+)"', webpage, 'ID')
        return self._extract_video(video_id)


class FranceTvInfoIE(FranceTVBaseInfoExtractor):
    IE_NAME = u'francetvinfo.fr'
    _VALID_URL = r'https?://www\.francetvinfo\.fr/replay.*/(?P<title>.+).html'

    _TEST = {
        u'url': u'http://www.francetvinfo.fr/replay-jt/france-3/soir-3/jt-grand-soir-3-lundi-26-aout-2013_393427.html',
        u'file': u'84981923.mp4',
        u'info_dict': {
            u'title': u'Soir 3',
        },
        u'params': {
            u'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_title = mobj.group('title')
        webpage = self._download_webpage(url, page_title)
        video_id = self._search_regex(r'id-video=(\d+?)"', webpage, u'video id')
        return self._extract_video(video_id)
