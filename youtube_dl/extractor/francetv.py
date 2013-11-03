# encoding: utf-8
import re
import xml.etree.ElementTree
import json

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


class France2IE(FranceTVBaseInfoExtractor):
    IE_NAME = u'france2.fr'
    _VALID_URL = r'''(?x)https?://www\.france2\.fr/
        (?:
            emissions/.*?/videos/(?P<id>\d+)
        |   emission/(?P<key>[^/?]+)
        )'''

    _TEST = {
        u'url': u'http://www.france2.fr/emissions/13h15-le-samedi-le-dimanche/videos/75540104',
        u'file': u'75540104.mp4',
        u'info_dict': {
            u'title': u'13h15, le samedi...',
            u'description': u'md5:2e5b58ba7a2d3692b35c792be081a03d',
        },
        u'params': {
            u'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj.group('key'):
            webpage = self._download_webpage(url, mobj.group('key'))
            video_id = self._html_search_regex(
                r'''(?x)<div\s+class="video-player">\s*
                    <a\s+href="http://videos.francetv.fr/video/([0-9]+)"\s+
                    class="francetv-video-player">''',
                webpage, u'video ID')
        else:
            video_id = mobj.group('id')
        return self._extract_video(video_id)


class GenerationQuoiIE(InfoExtractor):
    IE_NAME = u'france2.fr:generation-quoi'
    _VALID_URL = r'https?://generation-quoi\.france2\.fr/portrait/(?P<name>.*)(\?|$)'

    _TEST = {
        u'url': u'http://generation-quoi.france2.fr/portrait/garde-a-vous',
        u'file': u'k7FJX8VBcvvLmX4wA5Q.mp4',
        u'info_dict': {
            u'title': u'Génération Quoi - Garde à Vous',
            u'uploader': u'Génération Quoi',
        },
        u'params': {
            # It uses Dailymotion
            u'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        info_url = compat_urlparse.urljoin(url, '/medias/video/%s.json' % name)
        info_json = self._download_webpage(info_url, name)
        info = json.loads(info_json)
        return self.url_result('http://www.dailymotion.com/video/%s' % info['id'],
            ie='Dailymotion')
