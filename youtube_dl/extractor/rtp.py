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


def decode_b64_url(code):
    decoded_url = re.match(r"[^[]*\[([^]]*)\]", code).groups()[0]
    return compat_b64decode(
        compat_urllib_parse_unquote(
            decoded_url.replace('"', '').replace('\'', '').replace(',', ''))).decode('utf-8')


class RTPIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:(?:www\.)?rtp\.pt/play/(?P<subarea>.*/)?p(?P<program_id>[0-9]+)/(?P<episode_id>e[0-9]+/)?)|(?:arquivos\.rtp\.pt/conteudos/))(?P<id>[^/?#]+)/?'
    _TESTS = [{
        'url': 'https://www.rtp.pt/play/p9165/e562949/por-do-sol',
        'info_dict': {
            'id': 'por-do-sol',
            'ext': 'mp4',
            'title': 'Pôr do Sol Episódio 1 - de 16 Ago 2021',
            'description': 'Madalena Bourbon de Linhaça vive atormentada pelo segredo que esconde desde 1990. Matilde Bourbon de Linhaça sonha fugir com o seu amor proibido. O en',
            'thumbnail': r're:^https?://.*\.jpg',
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

        # Replace irrelevant text in title
        title = title.replace(' - RTP Play - RTP', '')

        # Check if it's a video split in parts, if so add part number to title
        part = self._html_search_regex(r'section\-parts.*<span.*>(.+?)</span>.*</ul>', webpage, 'part', default=None)
        if part:
            title = f'{title} {part}'

        # Get JS object
        js_object = self._search_regex(r'(?s)RTPPlayer *\( *({.+?}) *\);', webpage, 'player config')
        json_string_for_config = ''
        full_url = None

        # Verify JS object since it isn't pure JSON and maybe it needs some tuning
        for line in js_object.splitlines():
            stripped_line = line.strip()

            # key == 'fileKey', then we found what we wanted
            if re.match(r'fileKey:', stripped_line):
                if re.match(r'fileKey: *""', stripped_line):
                    raise ExtractorError("Episode not found (probably removed)", expected=True)
                url = decode_b64_url(stripped_line)
                if 'mp3' in url:
                    full_url = 'https://cdn-ondemand.rtp.pt' + url
                else:
                    full_url = 'https://streaming-vod.rtp.pt/dash{}/manifest.mpd'.format(url)

            elif not stripped_line.startswith("//") and not re.match('file *:', stripped_line) and not re.match('.*extraSettings ?:', stripped_line):
                # Ignore commented lines, `extraSettings` and `f`. The latter seems to some random unrelated video.
                json_string_for_config += '\n' + line

        if not full_url:
            raise ExtractorError("No valid media source found in page")

        # Finally send pure JSON string for JSON parsing
        config = self._parse_json(json_string_for_config, video_id, js_to_json)
        full_url = full_url.replace('drm-dash', 'dash')
        ext = determine_ext(full_url)

        if ext == 'mpd':
            # Download via mpd file
            formats = self._extract_mpd_formats(full_url, video_id)
            self._sort_formats(formats)
        else:
            formats = [{
                'url': full_url,
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
