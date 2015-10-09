from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    ExtractorError,
)


class ESPNIE(InfoExtractor):
    _VALID_URL = r'https?://espn\.go\.com/(?:[^/]+/)*(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://espn.go.com/video/clip?id=10365079',
        'info_dict': {
            'id': '10365079',
            'ext': 'mp4',
            'title': '30 for 30 Shorts: Judging Jewell',
            'description': 'On July 27, 1996, a terrorist\'s bomb exploded in a crowded Centennial Olympic Park during the Atlanta Olympic Games. The death toll might have been far higher if not for security guard Richard Jewell, who hours after his heroism was called a murderer.',
            'duration': 1302,
            'timestamp': 1390936111,
            'upload_date': '20140128',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'https://espn.go.com/video/iframe/twitter/?cms=espn&id=10365079',
        'only_matching': True,
    }, {
        'url': 'http://espn.go.com/nba/recap?gameId=400793786',
        'only_matching': True,
    }, {
        'url': 'http://espn.go.com/blog/golden-state-warriors/post/_/id/593/how-warriors-rapidly-regained-a-winning-edge',
        'only_matching': True,
    }, {
        'url': 'http://espn.go.com/sports/endurance/story/_/id/12893522/dzhokhar-tsarnaev-sentenced-role-boston-marathon-bombings',
        'only_matching': True,
    }, {
        'url': 'http://espn.go.com/nba/playoffs/2015/story/_/id/12887571/john-wall-washington-wizards-no-swelling-left-hand-wrist-game-5-return',
        'only_matching': True,
    }]

    def _extract_video_info(self, video_data):
        video_id = str(video_data['id'])
        formats = []
        for source in video_data['links']['source'].values():
            if isinstance(source, dict) and source.get('href'):
                source_url = source['href']
                if '.m3u8' in source_url:
                    formats.extend(self._extract_m3u8_formats(source_url, video_id, m3u8_id='hls'))
                elif '.f4m' in source_url:
                    formats.extend(self._extract_f4m_formats(source_url + '?hdcore=2.10.3', video_id, f4m_id='hds'))
                elif '.smil' in source_url:
                    formats.extend(self._extract_smil_formats(source_url, video_id))
                else:
                    formats.append({
                        'url': source_url,
                    })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_data['headline'],
            'description': video_data.get('description') or video_data.get('caption'),
            'duration': video_data.get('duration'),
            'thumbnail': video_data.get('thumbnail'),
            'timestamp': parse_iso8601(video_data.get('originalPublishDate')),
            'formats': formats,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url + ('&xhr=1' if '?' in url else '?xhr=1'), video_id)
        json_data = self._parse_json(webpage, video_id, fatal=False)
        if json_data:
            page_type = json_data['meta']['type']
            if page_type == 'video':
                return self._extract_video_info(json_data['content'])
            else:
                videos_data = json_data['content'].get('video')
                if videos_data:
                    entries = []
                    for video_data in videos_data:
                        entries.append(self._extract_video_info(video_data))
                    return self.playlist_result(entries, str(json_data['uid']), json_data['content']['title'], json_data['content']['description'])
                else:
                    raise ExtractorError('No videos in the webpage', expected=True)
        else:
            return self.url_result(self._search_regex(r'mobileLink\s*=\s*"([^"]+)";', webpage, 'mobile link'), 'ESPN')
