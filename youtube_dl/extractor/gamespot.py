from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urlparse,
    unescapeHTML,
    get_meta_content,
)


class GameSpotIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?gamespot\.com/.*-(?P<page_id>\d+)/?'
    _TEST = {
        "url": "http://www.gamespot.com/arma-iii/videos/arma-iii-community-guide-sitrep-i-6410818/",
        "file": "gs-2300-6410818.mp4",
        "md5": "b2a30deaa8654fcccd43713a6b6a4825",
        "info_dict": {
            "title": "Arma 3 - Community Guide: SITREP I",
            'description': 'Check out this video where some of the basics of Arma 3 is explained.',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_id = mobj.group('page_id')
        webpage = self._download_webpage(url, page_id)
        data_video_json = self._search_regex(r'data-video=["\'](.*?)["\']', webpage, 'data video')
        data_video = json.loads(unescapeHTML(data_video_json))

        # Transform the manifest url to a link to the mp4 files
        # they are used in mobile devices.
        f4m_url = data_video['videoStreams']['f4m_stream']
        f4m_path = compat_urlparse.urlparse(f4m_url).path
        QUALITIES_RE = r'((,\d+)+,?)'
        qualities = self._search_regex(QUALITIES_RE, f4m_path, 'qualities').strip(',').split(',')
        http_path = f4m_path[1:].split('/', 1)[1]
        http_template = re.sub(QUALITIES_RE, r'%s', http_path)
        http_template = http_template.replace('.csmil/manifest.f4m', '')
        http_template = compat_urlparse.urljoin('http://video.gamespotcdn.com/', http_template)
        formats = []
        for q in qualities:
            formats.append({
                'url': http_template % q,
                'ext': 'mp4',
                'format_id': q,
            })

        return {
            'id': data_video['guid'],
            'title': compat_urllib_parse.unquote(data_video['title']),
            'formats': formats,
            'description': get_meta_content('description', webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
