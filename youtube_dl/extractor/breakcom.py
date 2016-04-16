from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_age_limit,
)


class BreakIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?break\.com/video/(?:[^/]+/)*.+-(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.break.com/video/when-girls-act-like-guys-2468056',
        'info_dict': {
            'id': '2468056',
            'ext': 'mp4',
            'title': 'When Girls Act Like D-Bags',
            'age_limit': 13,
        }
    }, {
        'url': 'http://www.break.com/video/ugc/baby-flex-2773063',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            'http://www.break.com/embed/%s' % video_id, video_id)
        info = json.loads(self._search_regex(
            r'var embedVars = ({.*})\s*?</script>',
            webpage, 'info json', flags=re.DOTALL))

        youtube_id = info.get('youtubeId')
        if youtube_id:
            return self.url_result(youtube_id, 'Youtube')

        formats = [{
            'url': media['uri'] + '?' + info['AuthToken'],
            'tbr': media['bitRate'],
            'width': media['width'],
            'height': media['height'],
        } for media in info['media'] if media.get('mediaPurpose') == 'play']

        if not formats:
            formats.append({
                'url': info['videoUri']
            })

        self._sort_formats(formats)

        duration = int_or_none(info.get('videoLengthInSeconds'))
        age_limit = parse_age_limit(info.get('audienceRating'))

        return {
            'id': video_id,
            'title': info['contentName'],
            'thumbnail': info['thumbUri'],
            'duration': duration,
            'age_limit': age_limit,
            'formats': formats,
        }
