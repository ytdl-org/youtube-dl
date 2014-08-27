from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unescapeHTML,
    find_xpath_attr,
)


class CSpanIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?c-span\.org/video/\?(?P<id>[0-9a-f]+)'
    IE_DESC = 'C-SPAN'
    _TESTS = [{
        'url': 'http://www.c-span.org/video/?313572-1/HolderonV',
        'md5': '8e44ce11f0f725527daccc453f553eb0',
        'info_dict': {
            'id': '315139',
            'ext': 'mp4',
            'title': 'Attorney General Eric Holder on Voting Rights Act Decision',
            'description': 'Attorney General Eric Holder spoke to reporters following the Supreme Court decision in Shelby County v. Holder in which the court ruled that the preclearance provisions of the Voting Rights Act could not be enforced until Congress established new guidelines for review.',
        },
        'skip': 'Regularly fails on travis, for unknown reasons',
    }, {
        'url': 'http://www.c-span.org/video/?c4486943/cspan-international-health-care-models',
        # For whatever reason, the served video alternates between
        # two different ones
        #'md5': 'dbb0f047376d457f2ab8b3929cbb2d0c',
        'info_dict': {
            'id': '340723',
            'ext': 'mp4',
            'title': 'International Health Care Models',
            'description': 'md5:7a985a2d595dba00af3d9c9f0783c967',
        }
    }, {
        'url': 'http://www.c-span.org/video/?318608-1/gm-ignition-switch-recall',
        'info_dict': {
            'id': '342759',
            'title': 'General Motors Ignition Switch Recall',
        },
        'playlist_duration_sum': 14855,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_id = mobj.group('id')
        webpage = self._download_webpage(url, page_id)
        video_id = self._search_regex(r'progid=\'?([0-9]+)\'?>', webpage, 'video id')

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

        doc = self._download_xml(
            'http://www.c-span.org/common/services/flashXml.php?programid=' + video_id,
            video_id)

        title = find_xpath_attr(doc, './/string', 'name', 'title').text
        thumbnail = find_xpath_attr(doc, './/string', 'name', 'poster').text

        files = data['video']['files']

        entries = [{
            'id': '%s_%d' % (video_id, partnum + 1),
            'title': (
                title if len(files) == 1 else
                '%s part %d' % (title, partnum + 1)),
            'url': unescapeHTML(f['path']['#text']),
            'description': description,
            'thumbnail': thumbnail,
            'duration': int_or_none(f.get('length', {}).get('#text')),
        } for partnum, f in enumerate(files)]

        return {
            '_type': 'playlist',
            'entries': entries,
            'title': title,
            'id': video_id,
        }
