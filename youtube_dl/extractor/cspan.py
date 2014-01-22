from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    unescapeHTML,
)


class CSpanIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?c-spanvideo\.org/program/(?P<name>.*)'
    IE_DESC = 'C-SPAN'
    _TEST = {
        'url': 'http://www.c-spanvideo.org/program/HolderonV',
        'file': '315139.mp4',
        'md5': '8e44ce11f0f725527daccc453f553eb0',
        'info_dict': {
            'title': 'Attorney General Eric Holder on Voting Rights Act Decision',
            'description': 'Attorney General Eric Holder spoke to reporters following the Supreme Court decision in [Shelby County v. Holder] in which the court ruled that the preclearance provisions of the Voting Rights Act could not be enforced until Congress established new guidelines for review.',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        prog_name = mobj.group('name')
        webpage = self._download_webpage(url, prog_name)
        video_id = self._search_regex(r'prog(?:ram)?id=(.*?)&', webpage, 'video id')

        title = self._html_search_regex(
            r'<!-- title -->\n\s*<h1[^>]*>(.*?)</h1>', webpage, 'title')
        description = self._og_search_description(webpage)

        info_url = 'http://c-spanvideo.org/videoLibrary/assets/player/ajax-player.php?os=android&html5=program&id=' + video_id
        data_json = self._download_webpage(
            info_url, video_id, 'Downloading video info')
        data = json.loads(data_json)

        url = unescapeHTML(data['video']['files'][0]['path']['#text'])

        return {
            'id': video_id,
            'title': title,
            'url': url,
            'description': description,
            'thumbnail': self._og_search_thumbnail(webpage),
        }
