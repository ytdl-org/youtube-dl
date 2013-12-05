# encoding: utf-8
import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
)


class FranceTVBaseInfoExtractor(InfoExtractor):
    def _extract_video(self, video_id):
        info = self._download_xml(
            'http://www.francetvinfo.fr/appftv/webservices/video/'
            'getInfosOeuvre.php?id-diffusion='
            + video_id, video_id, 'Downloading XML config')

        manifest_url = info.find('videos/video/url').text
        video_url = manifest_url.replace('manifest.f4m', 'index_2_av.m3u8')
        video_url = video_url.replace('/z/', '/i/')
        thumbnail_path = info.find('image').text

        return {'id': video_id,
                'ext': 'flv' if video_url.startswith('rtmp') else 'mp4',
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
    _VALID_URL = r'https?://www\.francetvinfo\.fr/replay.*/(?P<title>.+)\.html'

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


class FranceTVIE(FranceTVBaseInfoExtractor):
    IE_NAME = u'francetv'
    IE_DESC = u'France 2, 3, 4, 5 and Ô'
    _VALID_URL = r'''(?x)https?://www\.france[2345o]\.fr/
        (?:
            emissions/.*?/(videos|emissions)/(?P<id>[^/?]+)
        |   (emissions?|jt)/(?P<key>[^/?]+)
        )'''

    _TESTS = [
        # france2
        {
            u'url': u'http://www.france2.fr/emissions/13h15-le-samedi-le-dimanche/videos/75540104',
            u'file': u'75540104.mp4',
            u'info_dict': {
                u'title': u'13h15, le samedi...',
                u'description': u'md5:2e5b58ba7a2d3692b35c792be081a03d',
            },
            u'params': {
                # m3u8 download
                u'skip_download': True,
            },
        },
        # france3
        {
            u'url': u'http://www.france3.fr/emissions/pieces-a-conviction/diffusions/13-11-2013_145575',
            u'info_dict': {
                u'id': u'000702326_CAPP_PicesconvictionExtrait313022013_120220131722_Au',
                u'ext': u'flv',
                u'title': u'Le scandale du prix des médicaments',
                u'description': u'md5:1384089fbee2f04fc6c9de025ee2e9ce',
            },
            u'params': {
                # rtmp download
                u'skip_download': True,
            },
        },
        # france4
        {
            u'url': u'http://www.france4.fr/emissions/hero-corp/videos/rhozet_herocorp_bonus_1_20131106_1923_06112013172108_F4',
            u'info_dict': {
                u'id': u'rhozet_herocorp_bonus_1_20131106_1923_06112013172108_F4',
                u'ext': u'flv',
                u'title': u'Hero Corp Making of - Extrait 1',
                u'description': u'md5:c87d54871b1790679aec1197e73d650a',
            },
            u'params': {
                # rtmp download
                u'skip_download': True,
            },
        },
        # france5
        {
            u'url': u'http://www.france5.fr/emissions/c-a-dire/videos/92837968',
            u'info_dict': {
                u'id': u'92837968',
                u'ext': u'mp4',
                u'title': u'C à dire ?!',
                u'description': u'md5:fb1db1cbad784dcce7c7a7bd177c8e2f',
            },
            u'params': {
                # m3u8 download
                u'skip_download': True,
            },
        },
        # franceo
        {
            u'url': u'http://www.franceo.fr/jt/info-afrique/04-12-2013',
            u'info_dict': {
                u'id': u'92327925',
                u'ext': u'mp4',
                u'title': u'Infô-Afrique',
                u'description': u'md5:ebf346da789428841bee0fd2a935ea55',
            },
            u'params': {
                # m3u8 download
                u'skip_download': True,
            },
            u'skip': u'The id changes frequently',
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj.group('key'):
            webpage = self._download_webpage(url, mobj.group('key'))
            id_res = [
                (r'''(?x)<div\s+class="video-player">\s*
                    <a\s+href="http://videos.francetv.fr/video/([0-9]+)"\s+
                    class="francetv-video-player">'''),
                (r'<a id="player_direct" href="http://info\.francetelevisions'
                 '\.fr/\?id-video=([^"/&]+)'),
                (r'<a class="video" id="ftv_player_(.+?)"'),
            ]
            video_id = self._html_search_regex(id_res, webpage, u'video ID')
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
