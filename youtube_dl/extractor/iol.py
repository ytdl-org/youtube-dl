# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re


class IOLIE(InfoExtractor):
    _VALID_URL = r'http://(tviplayer|(www\.tvi24))\.iol\.pt/.*/(?P<id>[0-9a-f]{24})($|\/)'
    _TESTS = [{
        'url': 'http://tviplayer.iol.pt/programa/euromilhoes/53c6b3153004dc006243b07b/video/55f878f90cf203f8b03cea6d',
        'md5': '983ca0edae370af67c458c6e5a71aae5',
        'info_dict': {
            'id': '55f878f90cf203f8b03cea6d',
            'ext': 'mp4',
            'title': u'Euromilhões - 15 de setembro de 2015',
            # 'tumbnail': 'http://www.iol.pt/multimedia/oratvi/multimedia/imagem/id/55f87a280cf2e6961770f01f',
            'description': u'Com Mónica Jardim'
        }
    }, {
        'url': 'http://tviplayer.iol.pt/programa/isso-e-tudo-muito-bonito-mas/55f30f2e0cf2a6b037fc1f2f/video/55f730c40cf23fa665481b18',
        'md5': 'ef5171a5abf69197726e5d7c7633c27a',
        'info_dict': {
            'id': '55f730c40cf23fa665481b18',
            'ext': 'mp4',
            'title': u'Isso é tudo muito bonito, mas: Concatena, filho, concatena',
            # 'tumbnail': 'http://www.iol.pt/multimedia/oratvi/multimedia/imagem/id/55f737330cf23fa665481b2d',
            'description': u'Quando os adversários unem perspectivas.'
        }
    }, {
        'url': 'http://www.tvi24.iol.pt/videos/passos-criacao-de-emprego-e-facto-muito-importante/55f816640cf2e6961770ef7a/2',
        'md5': 'd836f1225c289c7987beddebe11619b9',
        'info_dict': {
            'id': '55f816640cf2e6961770ef7a',
            'ext': 'mp4',
            'title': u'Passos: criação de emprego é facto muito importante',
            # 'tumbnail': 'http://www.iol.pt/multimedia/oratvi/multimedia/imagem/id/55f8180e0cf21413dfb1d96d/',
            'description': u'PM sublinha que é o nível mais elevado de há vários anos'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        title = re.sub(r' \| TVI Player$', '', title, re.IGNORECASE)

        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        m3u8_url = self._html_search_regex(r'''videoUrl:\s*'([^']+\.m3u8[^']*)'\s*,''', webpage, 'm3u8 playlist')
        formats = self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4')

        multimedia_id = self._html_search_meta('iol:id', webpage, 'multimedia_id', fatal=False, default=None)
        if multimedia_id is None:
            match = re.search(r'smil:([0-9a-f]{24})-L', m3u8_url, re.IGNORECASE)
            self.report_extraction('multimedia_id (fallback)')
            if match:
                multimedia_id = match.group(1)

        if multimedia_id is not None:
            m3u8_url_default = 'http://video-on-demand.iol.pt/vod_http/mp4:' + multimedia_id + '-L-500k.mp4/playlist.m3u8'
            formats_m3u8_default = self._extract_m3u8_formats(m3u8_url_default, video_id, ext='mp4')
            formats.extend(formats_m3u8_default)
            formats.append({
                'url': 'http://www.iol.pt/videos-file/' + multimedia_id + '-L-500k.mp4',
                'format_id': 'http_500',
                'tbr': 500,
                'protocol': 'http',
                'preference': -1,
                'no_resume': False
            })

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats
        }


class IOLStreamIE(IOLIE):
    _VALID_URL = r'http://tviplayer\.iol\.pt/direto/(?P<id>\S+)'
    _TESTS = [{
        'url': 'http://tviplayer.iol.pt/direto/TVI',
        'info_dict': {
            'id': 'TVI',
            'ext': 'mp4',
            'title': 're:^Direto TVI',
            'description': u'A TVI ao pé de si. Sempre.',
            'is_live': True,
        }
    }]

    def _real_extract(self, url):
        ret = IOLIE._real_extract(self, url)
        ret['is_live'] = True
        ret['title'] = self._live_title(ret['title'])

        return ret
