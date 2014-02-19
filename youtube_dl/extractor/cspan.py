from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unescapeHTML,
    find_xpath_attr,
)


class CSpanIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?c-span\.org/video/\?(?P<id>\d+)'
    IE_DESC = 'C-SPAN'
    _TEST = {
        'url': 'http://www.c-span.org/video/?313572-1/HolderonV',
        'md5': '8e44ce11f0f725527daccc453f553eb0',
        'info_dict': {
            'id': '315139',
            'ext': 'mp4',
            'title': 'Attorney General Eric Holder on Voting Rights Act Decision',
            'description': 'Attorney General Eric Holder spoke to reporters following the Supreme Court decision in Shelby County v. Holder in which the court ruled that the preclearance provisions of the Voting Rights Act could not be enforced until Congress established new guidelines for review.',
        },
        'skip': 'Regularly fails on travis, for unknown reasons',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_id = mobj.group('id')
        webpage = self._download_webpage(url, page_id)
        video_id = self._search_regex(r'data-progid=\'(\d+)\'>', webpage, 'video id')

        description = self._html_search_regex(
            [
                # The full description
                r'<div class=\'expandable\'>(.*?)<a href=\'#\'',
                # If the description is small enough the other div is not
                # present, otherwise this is a stripped version
                r'<p class=\'initial\'>(.*?)</p>'
            ],
            webpage, 'description', flags=re.DOTALL)

        info_url = 'http://c-spanvideo.org/videoLibrary/assets/player/ajax-player.php?os=android&html5=program&id=' + video_id
        data = self._download_json(info_url, video_id)

        url = unescapeHTML(data['video']['files'][0]['path']['#text'])

        doc = self._download_xml('http://www.c-span.org/common/services/flashXml.php?programid=' + video_id,
            video_id)

        def find_string(s):
            return find_xpath_attr(doc, './/string', 'name', s).text

        return {
            'id': video_id,
            'title': find_string('title'),
            'url': url,
            'description': description,
            'thumbnail': find_string('poster'),
        }
