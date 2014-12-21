from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    find_xpath_attr,
    fix_xml_ampersands
)


class ClipsyndicateIE(InfoExtractor):
    _VALID_URL = r'http://www\.clipsyndicate\.com/video/play(list/\d+)?/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.clipsyndicate.com/video/play/4629301/brick_briscoe',
        'md5': '4d7d549451bad625e0ff3d7bd56d776c',
        'info_dict': {
            'id': '4629301',
            'ext': 'mp4',
            'title': 'Brick Briscoe',
            'duration': 612,
            'thumbnail': 're:^https?://.+\.jpg',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        js_player = self._download_webpage(
            'http://eplayer.clipsyndicate.com/embed/player.js?va_id=%s' % video_id,
            video_id, 'Downlaoding player')
        # it includes a required token
        flvars = self._search_regex(r'flvars: "(.*?)"', js_player, 'flvars')

        pdoc = self._download_xml(
            'http://eplayer.clipsyndicate.com/osmf/playlist?%s' % flvars,
            video_id, 'Downloading video info',
            transform_source=fix_xml_ampersands)

        track_doc = pdoc.find('trackList/track')

        def find_param(name):
            node = find_xpath_attr(track_doc, './/param', 'name', name)
            if node is not None:
                return node.attrib['value']

        return {
            'id': video_id,
            'title': find_param('title'),
            'url': track_doc.find('location').text,
            'thumbnail': find_param('thumbnail'),
            'duration': int(find_param('duration')),
        }
