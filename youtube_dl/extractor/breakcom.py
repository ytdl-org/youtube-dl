from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class BreakIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?break\.com/video/(?:[^/]+/)*.+-(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.break.com/video/when-girls-act-like-guys-2468056',
        'md5': '33aa4ff477ecd124d18d7b5d23b87ce5',
        'info_dict': {
            'id': '2468056',
            'ext': 'mp4',
            'title': 'When Girls Act Like D-Bags',
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
        video_url = info['videoUri']
        youtube_id = info.get('youtubeId')
        if youtube_id:
            return self.url_result(youtube_id, 'Youtube')

        final_url = video_url + '?' + info['AuthToken']
        return {
            'id': video_id,
            'url': final_url,
            'title': info['contentName'],
            'thumbnail': info['thumbUri'],
        }
