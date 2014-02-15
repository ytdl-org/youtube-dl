# encoding: utf-8

from __future__ import unicode_literals

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
    IE_NAME = 'pluzz.francetv.fr'
    _VALID_URL = r'https?://pluzz\.francetv\.fr/videos/(.*?)\.html'

    # Can't use tests, videos expire in 7 days

    def _real_extract(self, url):
        title = re.match(self._VALID_URL, url).group(1)
        webpage = self._download_webpage(url, title)
        video_id = self._search_regex(
            r'data-diffusion="(\d+)"', webpage, 'ID')
        return self._extract_video(video_id)


class FranceTvInfoIE(FranceTVBaseInfoExtractor):
    IE_NAME = 'francetvinfo.fr'
    _VALID_URL = r'https?://www\.francetvinfo\.fr/replay.*/(?P<title>.+)\.html'

    _TEST = {
        'url': 'http://www.francetvinfo.fr/replay-jt/france-3/soir-3/jt-grand-soir-3-lundi-26-aout-2013_393427.html',
        'file': '84981923.mp4',
        'info_dict': {
            'title': 'Soir 3',
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_title = mobj.group('title')
        webpage = self._download_webpage(url, page_title)
        video_id = self._search_regex(r'id-video=(\d+?)[@"]', webpage, 'video id')
        return self._extract_video(video_id)


class FranceTVIE(FranceTVBaseInfoExtractor):
    IE_NAME = 'francetv'
    IE_DESC = 'France 2, 3, 4, 5 and Ô'
    _VALID_URL = r'''(?x)https?://www\.france[2345o]\.fr/
        (?:
            emissions/.*?/(videos|emissions)/(?P<id>[^/?]+)
        |   (emissions?|jt)/(?P<key>[^/?]+)
        )'''

    _TESTS = [
        # france2
        {
            'url': 'http://www.france2.fr/emissions/13h15-le-samedi-le-dimanche/videos/75540104',
            'file': '75540104.mp4',
            'info_dict': {
                'title': '13h15, le samedi...',
                'description': 'md5:2e5b58ba7a2d3692b35c792be081a03d',
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        # france3
        {
            'url': 'http://www.france3.fr/emissions/pieces-a-conviction/diffusions/13-11-2013_145575',
            'info_dict': {
                'id': '000702326_CAPP_PicesconvictionExtrait313022013_120220131722_Au',
                'ext': 'flv',
                'title': 'Le scandale du prix des médicaments',
                'description': 'md5:1384089fbee2f04fc6c9de025ee2e9ce',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        # france4
        {
            'url': 'http://www.france4.fr/emissions/hero-corp/videos/rhozet_herocorp_bonus_1_20131106_1923_06112013172108_F4',
            'info_dict': {
                'id': 'rhozet_herocorp_bonus_1_20131106_1923_06112013172108_F4',
                'ext': 'flv',
                'title': 'Hero Corp Making of - Extrait 1',
                'description': 'md5:c87d54871b1790679aec1197e73d650a',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        # france5
        {
            'url': 'http://www.france5.fr/emissions/c-a-dire/videos/92837968',
            'info_dict': {
                'id': '92837968',
                'ext': 'mp4',
                'title': 'C à dire ?!',
                'description': 'md5:fb1db1cbad784dcce7c7a7bd177c8e2f',
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        # franceo
        {
            'url': 'http://www.franceo.fr/jt/info-afrique/04-12-2013',
            'info_dict': {
                'id': '92327925',
                'ext': 'mp4',
                'title': 'Infô-Afrique',
                'description': 'md5:ebf346da789428841bee0fd2a935ea55',
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
            'skip': 'The id changes frequently',
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
            video_id = self._html_search_regex(id_res, webpage, 'video ID')
        else:
            video_id = mobj.group('id')
        return self._extract_video(video_id)


class GenerationQuoiIE(InfoExtractor):
    IE_NAME = 'france2.fr:generation-quoi'
    _VALID_URL = r'https?://generation-quoi\.france2\.fr/portrait/(?P<name>.*)(\?|$)'

    _TEST = {
        'url': 'http://generation-quoi.france2.fr/portrait/garde-a-vous',
        'file': 'k7FJX8VBcvvLmX4wA5Q.mp4',
        'info_dict': {
            'title': 'Génération Quoi - Garde à Vous',
            'uploader': 'Génération Quoi',
        },
        'params': {
            # It uses Dailymotion
            'skip_download': True,
        },
        'skip': 'Only available from France',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        info_url = compat_urlparse.urljoin(url, '/medias/video/%s.json' % name)
        info_json = self._download_webpage(info_url, name)
        info = json.loads(info_json)
        return self.url_result('http://www.dailymotion.com/video/%s' % info['id'],
            ie='Dailymotion')


class CultureboxIE(FranceTVBaseInfoExtractor):
    IE_NAME = 'culturebox.francetvinfo.fr'
    _VALID_URL = r'https?://culturebox\.francetvinfo\.fr/(?P<name>.*?)(\?|$)'

    _TEST = {
        'url': 'http://culturebox.francetvinfo.fr/einstein-on-the-beach-au-theatre-du-chatelet-146813',
        'info_dict': {
            'id': 'EV_6785',
            'ext': 'mp4',
            'title': 'Einstein on the beach au Théâtre du Châtelet',
            'description': 'md5:9ce2888b1efefc617b5e58b3f6200eeb',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        webpage = self._download_webpage(url, name)
        video_id = self._search_regex(r'"http://videos\.francetv\.fr/video/(.*?)"', webpage, 'video id')
        return self._extract_video(video_id)
