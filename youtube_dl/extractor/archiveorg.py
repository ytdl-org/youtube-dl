from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
)


class ArchiveOrgIE(InfoExtractor):
    IE_NAME = 'archive.org'
    IE_DESC = 'archive.org videos'
    _VALID_URL = r'(?:https?://)?(?:www\.)?archive\.org/details/(?P<id>[^?/]+)(?:[?].*)?$'
    _TEST = {
        "url": "http://archive.org/details/XD300-23_68HighlightsAResearchCntAugHumanIntellect",
        'file': 'XD300-23_68HighlightsAResearchCntAugHumanIntellect.ogv',
        'md5': '8af1d4cf447933ed3c7f4871162602db',
        'info_dict': {
            "title": "1968 Demo - FJCC Conference Presentation Reel #1",
            "description": "Reel 1 of 3: Also known as the \"Mother of All Demos\", Doug Engelbart's presentation at the Fall Joint Computer Conference in San Francisco, December 9, 1968 titled \"A Research Center for Augmenting Human Intellect.\" For this presentation, Doug and his team astonished the audience by not only relating their research, but demonstrating it live. This was the debut of the mouse, interactive computing, hypermedia, computer supported software engineering, video teleconferencing, etc. See also <a href=\"http://dougengelbart.org/firsts/dougs-1968-demo.html\" rel=\"nofollow\">Doug's 1968 Demo page</a> for more background, highlights, links, and the detailed paper published in this conference proceedings. Filmed on 3 reels: Reel 1 | <a href=\"http://www.archive.org/details/XD300-24_68HighlightsAResearchCntAugHumanIntellect\" rel=\"nofollow\">Reel 2</a> | <a href=\"http://www.archive.org/details/XD300-25_68HighlightsAResearchCntAugHumanIntellect\" rel=\"nofollow\">Reel 3</a>",
            "upload_date": "19681210",
            "uploader": "SRI International"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        json_url = url + ('?' if '?' in url else '&') + 'output=json'
        json_data = self._download_webpage(json_url, video_id)
        data = json.loads(json_data)

        title = data['metadata']['title'][0]
        description = data['metadata']['description'][0]
        uploader = data['metadata']['creator'][0]
        upload_date = unified_strdate(data['metadata']['date'][0])

        formats = [
            {
                'format': fdata['format'],
                'url': 'http://' + data['server'] + data['dir'] + fn,
                'file_size': int(fdata['size']),
            }
            for fn, fdata in data['files'].items()
            if 'Video' in fdata['format']]

        self._sort_formats(formats)

        return {
            '_type': 'video',
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'uploader': uploader,
            'upload_date': upload_date,
            'thumbnail': data.get('misc', {}).get('image'),
        }
