# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import (

    str_to_int,
    parse_iso8601,



)

class SnotrIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?snotr\.com/video/(?P<id>\d+)/([\w]+)'
    _TESTS =[ {
        'url': 'http://www.snotr.com/video/13708/Drone_flying_through_fireworks',
        'info_dict': {
            'id': '13708',
            'ext': 'flv',
            'title': 'Drone flying through fireworks!',
            'duration': 247,
            'filesize':12320768
          }
    },



        {

        'url': 'http://www.snotr.com/video/530/David_Letteman_-_George_W_Bush_Top_10',
        'info_dict': {
            'id': '530',
            'ext': 'flv',
            'title': 'David Letteman - George W. Bush Top 10',
            'duration': 126,
            'filesize': 1048576
           }
     }]


    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        # TODO more code goes here, for example ...
        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage)

        description = self._og_search_description(webpage)

        video_url = "http://cdn.videos.snotr.com/%s.flv" % video_id

        view_count = str_to_int(self._html_search_regex(r'<p>\n<strong>Views:</strong>\n([\d,\.]+)</p>',webpage,'view count'))

        duration = self._html_search_regex(r'<p>\n<strong>Length:</strong>\n(.*?)</p>',webpage,'duration')
        duration = str_to_int(duration[:1])*60 + str_to_int(duration[2:4])

        file_size = self._html_search_regex(r'<p>\n<strong>Filesize:</strong>\n(.*?)</p>',webpage,'filesize')
        file_size = str_to_int(re.match(r'\d+',file_size).group())*131072

        return {
            'id': video_id,
            'title': title,
            'url':video_url,
            'view_count':view_count,
            'duration':duration,
            'filesize':file_size

        }