# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
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
        'url': 'https://www.rtp.pt/play/p117/e476527/os-contemporaneos',
        'info_dict': {
            'id': 'os-contemporaneos',
            'ext': 'mp4',
            'title': 'Os Contemporâneos Episódio 1 -  RTP Play - RTP',
            'description': 'Os Contemporâneos, um programa de humor com um olhar na sociedade portuguesa!',
            'thumbnail': r're:^https?://.*\.jpg',
        },
    }, {
        'url': 'https://www.rtp.pt/play/p510/aleixo-fm',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        # Get JS object
        js_object = self._search_regex(r'(?s)RTPPlayer *\( *({.+?}) *\);', webpage, 'player config')

        json_string_for_config = ''

        # Verify JS object since it isn't pure JSON and maybe it needs some decodings
        for line in js_object.splitlines():
            stripped_line = line.strip()

            # If JS object key is 'file'
            if re.match('file ?:', stripped_line):
                if 'decodeURIComponent' in stripped_line:
                    # 1) The file URL is inside object and with HLS encoded...
                    hls_encoded = re.match(r"[^[]*\[([^]]*)\]", stripped_line).groups()[0]
                    hls_encoded = hls_encoded.replace('"', '').replace('\'', '').replace(',', '')
                    if 'atob' in stripped_line:
                        decoded_file_url = compat_b64decode(
                            compat_urllib_parse_unquote(
                                hls_encoded.replace('"', '').replace(',', ''))).decode('utf-8')
                    else:
                        decoded_file_url = compat_urllib_parse_unquote(hls_encoded)

                    # Insert the decoded HLS file URL into pure JSON string
                    json_string_for_config += '\nfile: "' + decoded_file_url + '",'
                else:
                    # 2) ... or the file URL is not encoded so keep it that way
                    json_string_for_config += '\n' + line

            elif not stripped_line.startswith("//") and not re.match('fileKey ?:', stripped_line) and not re.match('.*extraSettings ?:', stripped_line):
                # Ignore commented lines, 'fileKey' entry since it is no longer supported by RTP and also 'extraSettings'
                json_string_for_config += '\n' + line

        # Finally send pure JSON string for JSON parsing
        config = self._parse_json(json_string_for_config, video_id, js_to_json)

        # Check if file URL is directly a string or is still inside object
        if isinstance(config['file'], str):
            file_url = config['file']
        else:
            file_url = config['file']['hls']

        ext = determine_ext(file_url)

        if ext == 'm3u8':
            # Download via m3u8 file
            formats = self._extract_m3u8_formats(
                file_url, video_id, 'mp4', 'm3u8_native',
                m3u8_id='hls')

            self._sort_formats(formats)
        else:
            formats = [{
                'url': file_url,
                'ext': ext,
            }]

        if config.get('mediaType') == 'audio':
            for f in formats:
                f['vcodec'] = 'none'

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': self._html_search_meta(['description', 'twitter:description'], webpage),
            'thumbnail': config.get('poster') or self._og_search_thumbnail(webpage),
        }
