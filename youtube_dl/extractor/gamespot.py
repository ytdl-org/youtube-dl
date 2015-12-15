from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
    compat_urlparse,
)
from ..utils import (
    unescapeHTML,
)


class GameSpotIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?gamespot\.com/.*-(?P<id>\d+)/?'
    _TESTS = [{
        'url': 'http://www.gamespot.com/videos/arma-3-community-guide-sitrep-i/2300-6410818/',
        'md5': 'b2a30deaa8654fcccd43713a6b6a4825',
        'info_dict': {
            'id': 'gs-2300-6410818',
            'ext': 'mp4',
            'title': 'Arma 3 - Community Guide: SITREP I',
            'description': 'Check out this video where some of the basics of Arma 3 is explained.',
        },
    }, {
        'url': 'http://www.gamespot.com/videos/the-witcher-3-wild-hunt-xbox-one-now-playing/2300-6424837/',
        'info_dict': {
            'id': 'gs-2300-6424837',
            'ext': 'flv',
            'title': 'The Witcher 3: Wild Hunt [Xbox ONE]  - Now Playing',
            'description': 'Join us as we take a look at the early hours of The Witcher 3: Wild Hunt and more.',
        },
    }]

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)
        data_video_json = self._search_regex(
            r'data-video=["\'](.*?)["\']', webpage, 'data video')
        data_video = json.loads(unescapeHTML(data_video_json))
        streams = data_video['videoStreams']

        formats = []
        f4m_url = streams.get('f4m_stream')
        if f4m_url is not None:
            # Transform the manifest url to a link to the mp4 files
            # they are used in mobile devices.
            f4m_path = compat_urlparse.urlparse(f4m_url).path
            QUALITIES_RE = r'((,\d+)+,?)'
            qualities = self._search_regex(QUALITIES_RE, f4m_path, 'qualities').strip(',').split(',')
            http_path = f4m_path[1:].split('/', 1)[1]
            http_template = re.sub(QUALITIES_RE, r'%s', http_path)
            http_template = http_template.replace('.csmil/manifest.f4m', '')
            http_template = compat_urlparse.urljoin(
                'http://video.gamespotcdn.com/', http_template)
            for q in qualities:
                formats.append({
                    'url': http_template % q,
                    'ext': 'mp4',
                    'format_id': q,
                })
        else:
            for quality in ['sd', 'hd']:
                # It's actually a link to a flv file
                flv_url = streams.get('f4m_{0}'.format(quality))
                if flv_url is not None:
                    formats.append({
                        'url': flv_url,
                        'ext': 'flv',
                        'format_id': quality,
                    })

        return {
            'id': data_video['guid'],
            'display_id': page_id,
            'title': compat_urllib_parse_unquote(data_video['title']),
            'formats': formats,
            'description': self._html_search_meta('description', webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
