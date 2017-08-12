from __future__ import unicode_literals

import os
import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
    compat_urllib_parse_unquote_plus,
    compat_urllib_parse_urlparse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    str_to_int,
)
from ..aes import (
    aes_decrypt_text
)


class PornTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?porntube\.com/videos/.*_(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.porntube.com/videos/brazilian-babe-loren-colombara_7091127',
        'md5': '2c0cf65fd77680915fab1843d38fc7c3',
        'info_dict': {
            'id': '7091127',
            'ext': 'mp4',
            'title': 'Brazilian babe Loren Colombara',
            'description': 'Watch Brazilian babe Loren Colombara and other porn movies on PornTube.com. Free Porn Videos in HD and Mobile Ready.',
            'age_limit': 18
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        linkDes = re.findall(
            u'icon-download"></i><button id=".*?" data-id="([0-9]+)" data-name="porntube" data-quality="([0-9]+)">[0-9]+p . (.*?)MB<', webpage)

        title = self._html_search_regex(
            r'<title>(.*?) [|] PornTube &reg;</title>', webpage, 'title')
        description = self._og_search_description(webpage)

        formats = []

        mediaid = linkDes[0][0]
        formatids = "+".join([x[1] for x in linkDes])
        sizeids = dict((x[1], x[2]) for x in linkDes)

        req = compat_urllib_request.Request("https://tkn.kodicdn.com/0000000%s/download/%s" % (
            mediaid, formatids), headers={'ORIGIN': "http://www.porntube.com"}, data=b'')
        res = self._download_json(req, video_id, "Downloading JSON metadata")

        for k, v in res.items():
            if v['status'] == 'success':
                size = float(sizeids[k]) * 1024 * 1024

                rep = {
                    'format_id': k,
                    'ext': 'mp4',
                    'resolution': "%sp" % k,
                    'filesize': size,
                    'url': v['token']
                }
                formats.append(rep)

        formats_sorted = sorted(formats, key=lambda f: int(f['format_id']))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats_sorted,
            'age_limit': 18
        }
