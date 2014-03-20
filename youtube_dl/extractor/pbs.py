from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import compat_urllib_request


class PBSIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://
        (?:
            # Direct video URL
            video\.pbs\.org/(?:viralplayer|video)/(?P<id>[0-9]+)/? |
            # Article with embedded player
           (?:www\.)?pbs\.org/(?:[^/]+/){2,5}(?P<presumptive_id>[^/]+)/?(?:$|[?\#]) |
           # Player
           video\.pbs\.org/partnerplayer/(?P<player_id>[^/]+)/
        )
    '''

    _TEST = {
        'url': 'http://www.pbs.org/tpt/constitution-usa-peter-sagal/watch/a-more-perfect-union/',
        'info_dict': {
            'id': '2365006249',
            'ext': 'mp4',
            'title': 'A More Perfect Union',
            'description': 'md5:ba0c207295339c8d6eced00b7c363c6a',
            'duration': 3190,
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        presumptive_id = mobj.group('presumptive_id')
        display_id = presumptive_id
        if presumptive_id:
            webpage = self._download_webpage(url, display_id)
            url = self._search_regex(
                r'<iframe\s+id=["\']partnerPlayer["\'].*?\s+src=["\'](.*?)["\']>',
                webpage, 'player URL')
            mobj = re.match(self._VALID_URL, url)

        player_id = mobj.group('player_id')
        if not display_id:
            display_id = player_id
        if player_id:
            player_page = self._download_webpage(
                url, display_id, note='Downloading player page',
                errnote='Could not download player page')
            video_id = self._search_regex(
                r'<div\s+id="video_([0-9]+)"', player_page, 'video ID')
        else:
            video_id = mobj.group('id')
            display_id = video_id

        info_url = 'http://video.pbs.org/videoInfo/%s?format=json' % video_id
        info = self._download_json(info_url, display_id)

        redir_url = compat_urllib_request.urlopen(info['recommended_encoding']['url']).geturl()
        base_url = '/'.join(redir_url.split('/')[0:len(redir_url.split('/'))-1])

        m3u8 = self._download_webpage(redir_url, display_id, note='Downloading m3u8 playlist')

        splitted_m3u8 = m3u8.splitlines()

        formats = []
        for line in splitted_m3u8:
            if line.startswith('#EXT-X-STREAM-INF'):
                bandwidth = self._search_regex(r'BANDWIDTH=(\d+)', line, 'bandwidth')
                codecs = self._search_regex(r'CODECS="(.+?)"', line, 'codecs')
                filename = splitted_m3u8[splitted_m3u8.index(line)+1]

                formats.append({
                    'format_id': re.sub(r'(.*)000', r'\1k', bandwidth),
                    'url': base_url+'/'+filename,
                    'protocol': 'm3u8',
                    'ext': 'mp4',
                    'format_note': 'Audio only' if codecs.split('.')[0] == 'mp4a' else 'Video',
                    'quality': int(bandwidth),
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': info['title'],
            'formats': formats,
            'description': info['program'].get('description'),
            'thumbnail': info.get('image_url'),
            'duration': info.get('duration'),
        }
