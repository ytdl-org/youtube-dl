from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class BreakIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?break\.com/video/([^/]+)'
    _TEST = {
        'url': 'http://www.break.com/video/when-girls-act-like-guys-2468056',
        'md5': 'a3513fb1547fba4fb6cfac1bffc6c46b',
        'info_dict': {
            'id': '2468056',
            'ext': 'mp4',
            'title': 'When Girls Act Like D-Bags',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1).split("-")[-1]
        embed_url = 'http://www.break.com/embed/%s' % video_id
        webpage = self._download_webpage(embed_url, video_id)
        info_json = self._search_regex(r'var embedVars = ({.*})\s*?</script>',
            webpage, 'info json', flags=re.DOTALL)
        info = json.loads(info_json)
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
