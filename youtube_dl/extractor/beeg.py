from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_chr,
    compat_ord,
    compat_urllib_parse_unquote,
)
from ..utils import (
    int_or_none,
    parse_iso8601,
)


class BeegIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?beeg\.com/(?P<id>\d+)'
    _TEST = {
        'url': 'http://beeg.com/5416503',
        'md5': '46c384def73b33dbc581262e5ee67cef',
        'info_dict': {
            'id': '5416503',
            'ext': 'mp4',
            'title': 'Sultry Striptease',
            'description': 'md5:d22219c09da287c14bed3d6c37ce4bc2',
            'timestamp': 1391813355,
            'upload_date': '20140207',
            'duration': 383,
            'tags': list,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            'https://api.beeg.com/api/v5/video/%s' % video_id, video_id)

        def split(o, e):
            def cut(s, x):
                n.append(s[:x])
                return s[x:]
            n = []
            r = len(o) % e
            if r > 0:
                o = cut(o, r)
            while len(o) > e:
                o = cut(o, e)
            n.append(o)
            return n

        def decrypt_key(key):
            # Reverse engineered from http://static.beeg.com/cpl/1105.js
            a = '5ShMcIQlssOd7zChAIOlmeTZDaUxULbJRnywYaiB'
            e = compat_urllib_parse_unquote(key)
            o = ''.join([
                compat_chr(compat_ord(e[n]) - compat_ord(a[n % len(a)]) % 21)
                for n in range(len(e))])
            return ''.join(split(o, 3)[::-1])

        def decrypt_url(encrypted_url):
            encrypted_url = self._proto_relative_url(
                encrypted_url.replace('{DATA_MARKERS}', ''), 'https:')
            key = self._search_regex(
                r'/key=(.*?)%2Cend=', encrypted_url, 'key', default=None)
            if not key:
                return encrypted_url
            return encrypted_url.replace(key, decrypt_key(key))

        formats = []
        for format_id, video_url in video.items():
            if not video_url:
                continue
            height = self._search_regex(
                r'^(\d+)[pP]$', format_id, 'height', default=None)
            if not height:
                continue
            formats.append({
                'url': decrypt_url(video_url),
                'format_id': format_id,
                'height': int(height),
            })
        self._sort_formats(formats)

        title = video['title']
        video_id = video.get('id') or video_id
        display_id = video.get('code')
        description = video.get('desc')

        timestamp = parse_iso8601(video.get('date'), ' ')
        duration = int_or_none(video.get('duration'))

        tags = [tag.strip() for tag in video['tags'].split(',')] if video.get('tags') else None

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'duration': duration,
            'tags': tags,
            'formats': formats,
            'age_limit': 18,
        }
