from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_str,
    clean_html,
)


class MovieClipsIE(InfoExtractor):
    _VALID_URL = r'https?://movieclips\.com/(?P<id>[\da-zA-Z]+)(?:-(?P<display_id>[\da-z-]+))?'
    _TEST = {
        'url': 'http://movieclips.com/Wy7ZU-my-week-with-marilyn-movie-do-you-love-me/',
        'info_dict': {
            'id': 'Wy7ZU',
            'display_id': 'my-week-with-marilyn-movie-do-you-love-me',
            'ext': 'mp4',
            'title': 'My Week with Marilyn - Do You Love Me?',
            'description': 'md5:e86795bd332fe3cff461e7c8dc542acb',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')
        show_id = display_id or video_id

        config = self._download_xml(
            'http://config.movieclips.com/player/config/%s' % video_id,
            show_id, 'Downloading player config')

        if config.find('./country-region').text == 'false':
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, config.find('./region_alert').text), expected=True)

        properties = config.find('./video/properties')
        smil_file = properties.attrib['smil_file']

        smil = self._download_xml(smil_file, show_id, 'Downloading SMIL')
        base_url = smil.find('./head/meta').attrib['base']

        formats = []
        for video in smil.findall('./body/switch/video'):
            vbr = int(video.attrib['system-bitrate']) / 1000
            src = video.attrib['src']
            formats.append({
                'url': base_url,
                'play_path': src,
                'ext': src.split(':')[0],
                'vbr': vbr,
                'format_id': '%dk' % vbr,
            })

        self._sort_formats(formats)

        title = '%s - %s' % (properties.attrib['clip_movie_title'], properties.attrib['clip_title'])
        description = clean_html(compat_str(properties.attrib['clip_description']))
        thumbnail = properties.attrib['image']
        categories = properties.attrib['clip_categories'].split(',')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'categories': categories,
            'formats': formats,
        }
