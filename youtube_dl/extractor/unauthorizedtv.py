# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class UnauthorizedTvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?unauthorized\.tv/programs/(?P<id>.+)'
    _TEST = {
        'url': 'https://www.unauthorized.tv/programs/owens-shorts?cid=231148',
        'md5': 'dd9a5b81b9704c68942c2584086dd73f',
        'info_dict': {
            'id': 'owens-shorts?cid=231148',
            'ext': 'mp4',
            'title': 'Millennials',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        cid = None

        if "?cid=" in video_id:
            cid = int(video_id[video_id.find('=') + 1:])

        html = self._download_webpage(url, video_id)

        csrf_token = self._html_search_meta(
            'csrf-token',
            html,
            'csrf token',
            default=None
        )

        headers = {
            'Referer': url,
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRF-Token': csrf_token,
        }

        chaptersJson = self._download_json(
            'https://www.unauthorized.tv/api/contents/%s' % video_id,
            video_id,
            headers=headers
        )

        chapters = '&ids[]='.join([str(x) for x in chaptersJson['chapters']])

        metadata = self._download_json(
            'https://www.unauthorized.tv/api/chapters?ids[]=%s' % chapters,
            video_id,
            headers=headers
        )

        if cid is None:
            video_title = metadata[0]['title']
            video_url = metadata[0]['subject']['versions']['hls']
        else:
            for item in metadata:
                if item["id"] == cid:
                    video_title = item['title']
                    video_url = item['subject']['versions']['hls']

        return {
            'id': video_id,
            'title': video_title,
            'url': video_url,
            'ext': 'mp4',
        }
