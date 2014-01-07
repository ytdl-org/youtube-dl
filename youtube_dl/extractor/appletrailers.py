from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    determine_ext,
)


class AppleTrailersIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?trailers\.apple\.com/trailers/(?P<company>[^/]+)/(?P<movie>[^/]+)'
    _TEST = {
        "url": "http://trailers.apple.com/trailers/wb/manofsteel/",
        "playlist": [
            {
                "file": "manofsteel-trailer4.mov",
                "md5": "d97a8e575432dbcb81b7c3acb741f8a8",
                "info_dict": {
                    "duration": 111,
                    "title": "Trailer 4",
                    "upload_date": "20130523",
                    "uploader_id": "wb",
                },
            },
            {
                "file": "manofsteel-trailer3.mov",
                "md5": "b8017b7131b721fb4e8d6f49e1df908c",
                "info_dict": {
                    "duration": 182,
                    "title": "Trailer 3",
                    "upload_date": "20130417",
                    "uploader_id": "wb",
                },
            },
            {
                "file": "manofsteel-trailer.mov",
                "md5": "d0f1e1150989b9924679b441f3404d48",
                "info_dict": {
                    "duration": 148,
                    "title": "Trailer",
                    "upload_date": "20121212",
                    "uploader_id": "wb",
                },
            },
            {
                "file": "manofsteel-teaser.mov",
                "md5": "5fe08795b943eb2e757fa95cb6def1cb",
                "info_dict": {
                    "duration": 93,
                    "title": "Teaser",
                    "upload_date": "20120721",
                    "uploader_id": "wb",
                },
            }
        ]
    }

    _JSON_RE = r'iTunes.playURL\((.*?)\);'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        movie = mobj.group('movie')
        uploader_id = mobj.group('company')

        playlist_url = compat_urlparse.urljoin(url, u'includes/playlists/itunes.inc')
        def fix_html(s):
            s = re.sub(r'(?s)<script[^<]*?>.*?</script>', u'', s)
            s = re.sub(r'<img ([^<]*?)>', r'<img \1/>', s)
            # The ' in the onClick attributes are not escaped, it couldn't be parsed
            # like: http://trailers.apple.com/trailers/wb/gravity/
            def _clean_json(m):
                return u'iTunes.playURL(%s);' % m.group(1).replace('\'', '&#39;')
            s = re.sub(self._JSON_RE, _clean_json, s)
            s = u'<html>' + s + u'</html>'
            return s
        doc = self._download_xml(playlist_url, movie, transform_source=fix_html)

        playlist = []
        for li in doc.findall('./div/ul/li'):
            on_click = li.find('.//a').attrib['onClick']
            trailer_info_json = self._search_regex(self._JSON_RE,
                on_click, u'trailer info')
            trailer_info = json.loads(trailer_info_json)
            title = trailer_info['title']
            video_id = movie + '-' + re.sub(r'[^a-zA-Z0-9]', '', title).lower()
            thumbnail = li.find('.//img').attrib['src']
            upload_date = trailer_info['posted'].replace('-', '')

            runtime = trailer_info['runtime']
            m = re.search(r'(?P<minutes>[0-9]+):(?P<seconds>[0-9]{1,2})', runtime)
            duration = None
            if m:
                duration = 60 * int(m.group('minutes')) + int(m.group('seconds'))

            first_url = trailer_info['url']
            trailer_id = first_url.split('/')[-1].rpartition('_')[0].lower()
            settings_json_url = compat_urlparse.urljoin(url, 'includes/settings/%s.json' % trailer_id)
            settings_json = self._download_webpage(settings_json_url, trailer_id, u'Downloading settings json')
            settings = json.loads(settings_json)

            formats = []
            for format in settings['metadata']['sizes']:
                # The src is a file pointing to the real video file
                format_url = re.sub(r'_(\d*p.mov)', r'_h\1', format['src'])
                formats.append({
                    'url': format_url,
                    'ext': determine_ext(format_url),
                    'format': format['type'],
                    'width': format['width'],
                    'height': int(format['height']),
                })

            self._sort_formats(formats)

            playlist.append({
                '_type': 'video',
                'id': video_id,
                'title': title,
                'formats': formats,
                'title': title,
                'duration': duration,
                'thumbnail': thumbnail,
                'upload_date': upload_date,
                'uploader_id': uploader_id,
                'user_agent': 'QuickTime compatible (youtube-dl)',
            })

        return {
            '_type': 'playlist',
            'id': movie,
            'entries': playlist,
        }
