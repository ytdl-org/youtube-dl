from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    fix_xml_ampersands,
)


class TNAFlixIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tnaflix\.com/(?P<cat_id>[^/]+)/(?P<display_id>[^/]+)/video(?P<id>\d+)'

    _TITLE_REGEX = r'<title>(.+?) - TNAFlix Porn Videos</title>'
    _DESCRIPTION_REGEX = r'<h3 itemprop="description">([^<]+)</h3>'
    _CONFIG_REGEX = r'flashvars\.config\s*=\s*escape\("([^"]+)"'

    _TEST = {
        'url': 'https://www.tnaflix.com/amateur-porn/bunzHD-Ms.Donk/video358632',
        'md5': '6c431ea56756497e227fb3f01a687869',
        'info_dict': {
            'id': '358632',
            'display_id': 'bunzHD-Ms.Donk',
            'ext': 'mp4',
            'title': 'bunzHD Ms.Donk',
            'description': 'bubble booty ebony teen goddess Ms.Donk has a firm ass and acts like she is shy but really she is a freak in the sheets watch her 20 min XX rated vid at bunzHD.com click on the catalog link',
            'thumbnail': 're:https?://.*\.jpg$',
            'duration': 394,
            'age_limit': 18,
        }
    }

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

        duration = self._html_search_meta('duration', webpage, 'duration', default=None)
        if duration:
            duration = parse_duration(duration[1:])

        cfg_url = self._proto_relative_url(self._html_search_regex(
            self._CONFIG_REGEX, webpage, 'flashvars.config'), 'http:')

        cfg_xml = self._download_xml(
            cfg_url, display_id, note='Downloading metadata',
            transform_source=fix_xml_ampersands)

        thumbnail = cfg_xml.find('./startThumb').text

        formats = []
        for item in cfg_xml.findall('./quality/item'):
            video_url = re.sub('speed=\d+', 'speed=', item.find('videoLink').text)
            format_id = item.find('res').text
            fmt = {
                'url': video_url,
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
