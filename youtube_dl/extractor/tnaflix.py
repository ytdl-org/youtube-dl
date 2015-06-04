from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    fix_xml_ampersands,
)


class TNAFlixIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tnaflix\.com/[^/]+/(?P<display_id>[^/]+)/video(?P<id>\d+)'

    _TITLE_REGEX = r'<title>(.+?) - TNAFlix Porn Videos</title>'
    _DESCRIPTION_REGEX = r'<h3 itemprop="description">([^<]+)</h3>'
    _CONFIG_REGEX = r'flashvars\.config\s*=\s*escape\("([^"]+)"'

    _TESTS = [
        {
            'url': 'http://www.tnaflix.com/porn-stars/Carmella-Decesare-striptease/video553878',
            'md5': 'ecf3498417d09216374fc5907f9c6ec0',
            'info_dict': {
                'id': '553878',
                'display_id': 'Carmella-Decesare-striptease',
                'ext': 'mp4',
                'title': 'Carmella Decesare - striptease',
                'description': '',
                'thumbnail': 're:https?://.*\.jpg$',
                'duration': 91,
                'age_limit': 18,
            }
        },
        {
            'url': 'https://www.tnaflix.com/amateur-porn/bunzHD-Ms.Donk/video358632',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        title = self._html_search_regex(
            self._TITLE_REGEX, webpage, 'title') if self._TITLE_REGEX else self._og_search_title(webpage)
        description = self._html_search_regex(
            self._DESCRIPTION_REGEX, webpage, 'description', fatal=False, default='')

        age_limit = self._rta_search(webpage)

        duration = parse_duration(self._html_search_meta(
            'duration', webpage, 'duration', default=None))

        cfg_url = self._proto_relative_url(self._html_search_regex(
            self._CONFIG_REGEX, webpage, 'flashvars.config'), 'http:')

        cfg_xml = self._download_xml(
            cfg_url, display_id, note='Downloading metadata',
            transform_source=fix_xml_ampersands)

        thumbnail = self._proto_relative_url(
            cfg_xml.find('./startThumb').text, 'http:')

        formats = []
        for item in cfg_xml.findall('./quality/item'):
            video_url = re.sub('speed=\d+', 'speed=', item.find('videoLink').text)
            format_id = item.find('res').text
            fmt = {
                'url': self._proto_relative_url(video_url, 'http:'),
                'format_id': format_id,
            }
            m = re.search(r'^(\d+)', format_id)
            if m:
                fmt['height'] = int(m.group(1))
            formats.append(fmt)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': age_limit,
            'formats': formats,
        }
