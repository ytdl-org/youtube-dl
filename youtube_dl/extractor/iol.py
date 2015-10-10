# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import js_to_json, ExtractorError

import re


class IOLIE(InfoExtractor):
    _VALID_URL = r'https?://[^/]*\.iol\.pt/.*/(?P<id>[0-9a-f]{24})($|\/)'
    _TESTS = [{
        'url': 'http://tviplayer.iol.pt/programa/euromilhoes/53c6b3153004dc006243b07b/video/55f878f90cf203f8b03cea6d',
        'md5': '983ca0edae370af67c458c6e5a71aae5',
        'info_dict': {
            'id': '55f878f90cf203f8b03cea6d',
            'ext': 'mp4',
            'title': u'Euromilhões - 15 de setembro de 2015',
            'thumbnail': 'http://www.iol.pt/multimedia/oratvi/multimedia/imagem/id/55f87a280cf2e6961770f01f',
            'description': u'Com Mónica Jardim'
        }
    }, {
        'url': 'http://tviplayer.iol.pt/programa/isso-e-tudo-muito-bonito-mas/55f30f2e0cf2a6b037fc1f2f/video/55f730c40cf23fa665481b18',
        'md5': 'ef5171a5abf69197726e5d7c7633c27a',
        'info_dict': {
            'id': '55f730c40cf23fa665481b18',
            'ext': 'mp4',
            'title': u'Isso é tudo muito bonito, mas: Concatena, filho, concatena',
            'thumbnail': 'http://www.iol.pt/multimedia/oratvi/multimedia/imagem/id/55f737330cf23fa665481b2d',
            'description': u'Quando os adversários unem perspectivas.'
        }
    }, {
        'url': 'http://www.tvi24.iol.pt/videos/passos-criacao-de-emprego-e-facto-muito-importante/55f816640cf2e6961770ef7a/2',
        'md5': 'd836f1225c289c7987beddebe11619b9',
        'info_dict': {
            'id': '55f816640cf2e6961770ef7a',
            'ext': 'mp4',
            'title': u'Passos: criação de emprego é facto muito importante',
            'thumbnail': 'http://www.iol.pt/multimedia/oratvi/multimedia/imagem/id/55f8180e0cf21413dfb1d96d/',
            'description': u'PM sublinha que é o nível mais elevado de há vários anos'
        }
    }, {
        'url': 'http://www.maisfutebol.iol.pt/videos/560b04f80cf25f02cc1d843f/fc-porto/lopetegui-nao-quer-faltar-ao-respeito-ao-maccabi',
        'md5': '738a970259469fbb54b2d391c4c69dab',
        'info_dict': {
            'id': '560b04f80cf25f02cc1d843f',
            'ext': 'mp4',
            'title': u'Lopetegui não quer «faltar ao respeito ao Maccabi»',
            'thumbnail': 'http://www.maisfutebol.iol.pt/multimedia/oratvi/multimedia/imagem/id/560b06c50cf2c14000fb838d/600',
            'description': u'Treinador do FC Porto e a possibilidade de disparar na tabela nos dois jogos com os israelitas.'
        }
    }, {
        'url': 'http://www.maisfutebol.iol.pt/videos/5611a7e30cf2d8d8759054eb/liga/perdi-uma-semana-com-ewerton',
        'md5': '9535c58831ecd4bbb95e600d34eaeef8',
        'info_dict': {
            'id': '5611a7e30cf2d8d8759054eb',
            'ext': 'mp4',
            'title': u'«Perdi uma semana com Ewerton»',
            'thumbnail': 'http://www.maisfutebol.iol.pt/multimedia/oratvi/multimedia/imagem/id/5611aa840cf20a9cbc0da934/600',
            'description': u'Treinador explica situação do central.'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        iol_js = self._html_search_regex(r'\.iolplayer\(\s*(\{.+?\})\s*\)', webpage, 'iolplayer', flags=re.DOTALL)

        # in a perfect world this would work but in practice it breaks too many times. RegExps are more "robust"
        try:
            iol_json = self._parse_json(iol_js, video_id, transform_source=js_to_json)
            m3u8_url = iol_json['videoUrl']
            title = iol_json.get('title', title)  # this title information has less cruft (defaults to _og_search_title)
        except ExtractorError:
            # need to parse using regexps
            m3u8_url = self._html_search_regex(r'''videoUrl:\s*'([^']+\.m3u8[^']*)'\s*,''', iol_js, 'm3u8 playlist (json fallback)')
            title_js = self._html_search_regex(r'''title:\s*'(.+?)'\s*,''', iol_js, 'title (json fallback)', fatal=False, default=None)
            if title_js is not None:
                title = title_js

        formats = self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4')

        multimedia_id = self._html_search_meta('iol:id', webpage, 'multimedia_id', fatal=False, default=None)
        if multimedia_id is None:
            multimedia_id = self._search_regex(r'smil:([0-9a-f]{24})-L', m3u8_url, 'multimedia_id (fallback)', flags=re.IGNORECASE, default=None, fatal=False)

        if multimedia_id is not None:
            m3u8_url_default = 'http://video-on-demand.iol.pt/vod_http/mp4:' + multimedia_id + '-L-500k.mp4/playlist.m3u8'
            formats_m3u8_default = self._extract_m3u8_formats(m3u8_url_default, video_id, ext='mp4')
            formats.extend(formats_m3u8_default)

            # try rtmp format
            if self._html_search_regex(r'<script\s+src\s*=\s*"([^"]*/cdn\.iol\.pt/js/iol\.js)"', webpage, "iol.js", fatal=False):
                server = 'video1.iol.pt'

                try:
                    # get actual server
                    xml = self._download_xml('http://www.iol.pt/videolb', video_id, note='Downloading server info XML', fatal=False)
                    if 'redirect' == xml.tag:
                        server = xml.text

                except Exception as ex:
                    # just ignore every error, rtmp is not essential
                    self.report_warning('RTMP server not found. %r' % (ex,))

                formats.append({
                    'url': 'rtmp://' + server + '/vod',
                    'play_path': 'mp4:' + multimedia_id + '-L-500k',
                    'format_id': 'rtmp-500',
                    'tbr': 500,
                    'protocol': 'rtmp'
                })

            formats.append({
                'url': 'http://www.iol.pt/videos-file/' + multimedia_id + '-L-500k.mp4',
                'format_id': 'http-500',
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
        # can't find uncluttered title information for live
        title = re.sub(r'\s*\|\s*TVI Player\s*$', '', ret['title'], re.IGNORECASE)
        ret['is_live'] = True
        ret['title'] = self._live_title(title)

        return ret
