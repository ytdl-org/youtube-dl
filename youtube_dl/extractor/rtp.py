# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    js_to_json,
)
from ..compat import (
    compat_b64decode,
    compat_urllib_parse_unquote,
)

import re


class RTPIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:(?:www\.)?rtp\.pt/play/(?P<subarea>.*/)?p(?P<program_id>[0-9]+)/(?P<episode_id>e[0-9]+/)?)|(?:arquivos\.rtp\.pt/conteudos/))(?P<id>[^/?#]+)/?'
    _TESTS = [{
        'url': 'https://www.rtp.pt/play/p117/e563265/os-contemporaneos',
        'info_dict': {
            'id': 'os-contemporaneos',
            'ext': 'mp4',
            'title': 'Os Contemporâneos Episódio 1',
            'description': 'Os Contemporâneos, um programa de humor com um olhar na sociedade portuguesa!',
            'thumbnail': r're:^https?://.*\.(jpg|png)'
        },
    }, {
        'url': 'https://www.rtp.pt/play/p8157/e541212/telejornal',
        'info_dict': {
            'id': 'telejornal',
            'ext': 'mp4',
            'title': 'Telejornal de 01 Mai 2021 PARTE 1',
            'description': 'A mais rigorosa seleção de notícias, todos os dias às 20h00. De segunda a domingo, João Adelino Faria e José Rodrigues dos Santos mostram-lhe o que de'
        },
    }, {
        'url': 'https://www.rtp.pt/play/p6646/e457262/grande-entrevista',
        'info_dict': {
            'id': 'grande-entrevista',
            'ext': 'mp4',
            'title': 'Grande Entrevista Episódio 7 - de 19 Fev 2020',
            'description': 'Bruno Nogueira - É um dos mais originais humoristas portugueses e de maior êxito! Bruno Nogueira na Grande Entrevista com Vítor Gonçalves.'
        },
    }, {
        'url': 'https://www.rtp.pt/play/estudoemcasa/p7776/e539826/portugues-1-ano',
        'info_dict': {
            'id': 'portugues-1-ano',
            'ext': 'mp4',
            'title': 'Português - 1.º ano , aula 45 -  27 Abr 2021 - Estudo Em Casa - RTP',
            'description': 'A História do Pedrito Coelho, de Beatrix Potter. O dígrafo \'lh\' - A História do Pedrito Coelho, de Beatrix Potter. O dígrafo \'lh\'.'
        },
    }, {
        'url': 'https://www.rtp.pt/play/zigzag/p5449/e385973/banda-zig-zag',
        'info_dict': {
            'id': 'banda-zig-zag',
            'ext': 'mp4',
            'title': 'Banda Zig Zag Episódio 1 -  Zig Zag Play - RTP',
            'description': 'A Amizade é o Nosso Mel - Zig: é a menina que além de tocar também canta. Adora aprender palavras novas e adora ler. Gosta de fazer palavras cruzadas'
        },
    }, {
        'url': 'https://arquivos.rtp.pt/conteudos/liga-dos-ultimos-152/',
        'info_dict': {
            'id': 'liga-dos-ultimos-152',
            'ext': 'mp4',
            'title': 'Liga dos Últimos – RTP Arquivos',
            'description': 'Magazine desportivo, com apresentação de Álvaro Costa e comentários em estúdio do professor Hernâni Gonçalves e do sociólogo João Nuno Coelho. Destaque para os jogos de futebol das equipas dos escalões secundários de Portugal, com momentos dos jogos: Agrário de Lamas vs Pampilhoense e Apúlia vs Fragoso.'
        },
    }, {
        'url': 'https://www.rtp.pt/play/p510/aleixo-fm',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        # Remove JS multi-line comments from webpage source
        webpage = re.sub(r'(\/\*.*\*\/)', '', webpage, flags=re.DOTALL)

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        if 'Este episódio não se encontra disponível' in title:
            raise ExtractorError('Episode unavailable', expected=True)

        # Replace irrelevant text in title
        title = re.sub(r' -  ?RTP Play - RTP', '', title)

        # Check if it's a video split in parts, if so add part number to title
        part = self._html_search_regex(r'section\-parts.*<span.*>(.+?)</span>.*</ul>', webpage, 'part', default=None)
        if part:
            title = '{title} {part}'.format(title=title, part=part)

        # Get JS object
        js_object = self._search_regex(r'(?s)RTPPlayer *\( *({.+?}) *\);', webpage, 'player config')

        json_string_for_config = ''
        filekey_found = False

        # Verify JS object since it isn't pure JSON and probably needs some fixing
        for line in js_object.splitlines():
            stripped_line = line.strip()

            # If JS object key is 'fileKey'
            if re.match('fileKey ?:', stripped_line):
                filekey_found = True
                if 'decodeURIComponent' in stripped_line:
                    # 1) The value is an encoded URL
                    encoded_url = re.match(r"[^[]*\[([^]]*)\]", stripped_line).groups()[0]
                    encoded_url = re.sub(r'[\s"\',]', '', encoded_url)

                    if 'atob' in stripped_line:
                        # Most of the times 'atob' approach is used but not always so we need to be sure
                        decoded_url = compat_b64decode(
                            compat_urllib_parse_unquote(
                                encoded_url)).decode('utf-8')
                    else:
                        # If no 'atob' we just need to unquote it
                        decoded_url = compat_urllib_parse_unquote(encoded_url)

                    # Insert the (relative) decoded URL in JSON
                    json_string_for_config += '\nfileKey: "{decoded_url}",'.format(decoded_url=decoded_url)
                else:
                    # 2) ... or the value URL is not encoded so keep it that way
                    json_string_for_config += '\n{stripped_line}'.format(stripped_line=stripped_line)

            elif (
                not stripped_line.startswith("//")
                and not re.match('.*extraSettings ?:', stripped_line)
                and (not filekey_found or (filekey_found and not re.match('file ?:', stripped_line)))
            ):
                # Ignore commented lines and 'extraSettings'. Also ignore 'file' if 'fileKey' already exists
                json_string_for_config += '\n{stripped_line}'.format(stripped_line=stripped_line)

        # Finally send pure JSON string for JSON parsing
        config = self._parse_json(json_string_for_config, video_id, js_to_json)

        if 'fileKey' in config:
            # 'fileKey' has priority over 'file' on our end
            file_url = config['fileKey']
        elif 'file' in config:
            # 'RTP Arquivos' still uses old regular non-encoded 'file' key
            file_url = config['file']
        else:
            raise ExtractorError('No valid media source found in page')

        ext = determine_ext(file_url)

        if ext == 'mp4':
            # Due to recent changes, we need to hardcode the URL like this and download it using 'm3u8'
            file_url = 'https://streaming-vod.rtp.pt/hls{file_url}/index-v1-a1.m3u8'.format(file_url=file_url)

            formats = self._extract_m3u8_formats(
                file_url, video_id, 'mp4', 'm3u8_native',
                m3u8_id='hls')
        elif ext == 'm3u8':
            # It can be downloaded without any further changes
            formats = self._extract_m3u8_formats(
                file_url, video_id, 'mp4', 'm3u8_native',
                m3u8_id='hls')
        else:
            # Need to set basepath
            file_url = 'https://cdn-ondemand.rtp.pt{file_url}'.format(file_url=file_url)
            formats = [{
                'url': file_url,
                'ext': ext,
            }]

        if config['mediaType'] == 'audio':
            for f in formats:
                f['vcodec'] = 'none'

        subtitles = {}
        if 'vtt' in config:
            sub_lang, sub_lang_full, sub_url = config['vtt'][0]
            subtitles.setdefault(sub_lang, []).append({
                'url': sub_url,
                'ext': 'vtt',
            })

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'description': self._html_search_meta(['og:description', 'description', 'twitter:description'], webpage),
            'thumbnail': config['poster'] or self._og_search_thumbnail(webpage),
        }
