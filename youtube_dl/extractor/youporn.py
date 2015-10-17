from __future__ import unicode_literals


import json
import re
import sys

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlparse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    unescapeHTML,
    unified_strdate,
)
from ..aes import (
    aes_decrypt_text
)


class YouPornIE(InfoExtractor):
    _VALID_URL = r'^(?P<proto>https?://)(?:www\.)?(?P<url>youporn\.com/watch/(?P<videoid>[0-9]+)/(?P<title>[^/]+))'
    _TEST = {
        'url': 'http://www.youporn.com/watch/505835/sex-ed-is-it-safe-to-masturbate-daily/',
        'info_dict': {
            'id': '505835',
            'ext': 'mp4',
            'title': 'Sex Ed: Is It Safe To Masturbate Daily?',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        url = mobj.group('proto') + 'www.' + mobj.group('url')

        req = compat_urllib_request.Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)
        age_limit = self._rta_search(webpage)

        self.report_extraction(video_id)
        try:
            video_title = self._html_search_regex(r'page_params.video_title = \'(.+?)\';', webpage, 'video URL')
        except KeyError:
            raise ExtractorError('Missing JSON parameter: ' + sys.exc_info()[1])

        # Get all of the links from the page
        DOWNLOAD_LIST_RE = r'(?s)<div id="downloadModal" class="modalBox">(?P<testje>.*?)<div id="embedModal" class="modalBox">'
        download_list_html = self._search_regex(DOWNLOAD_LIST_RE, webpage, 'testje').strip()
        LINK_RE = r'<a href=\'([^"]+)\' title=\'Download Video\'>'
        links = re.findall(LINK_RE, download_list_html)

        # Get all encrypted links
        encrypted_links = re.findall(r'encryptedQuality[0-9]{3}URL\t=\t\'([a-zA-Z0-9+/]+={0,2})\';', webpage)
        for encrypted_link in encrypted_links:
            link = aes_decrypt_text(encrypted_link, video_title, 32).decode('utf-8')
            links.append(link)

        formats = []
        for link in links:
            # A link looks like this:
            # http://cdn1.download.youporn.phncdn.com/201210/31/8004515/480p_370k_8004515/YouPorn%20-%20Nubile%20Films%20The%20Pillow%20Fight.mp4?nvb=20121113051249&nva=20121114051249&ir=1200&sr=1200&hash=014b882080310e95fb6a0
            # A path looks like this:
            # /201210/31/8004515/480p_370k_8004515/YouPorn%20-%20Nubile%20Films%20The%20Pillow%20Fight.mp4
            video_url = unescapeHTML(link)
            path = compat_urllib_parse_urlparse(video_url).path
            format_parts = path.split('/')[4].split('_')[:2]

            dn = compat_urllib_parse_urlparse(video_url).netloc.partition('.')[0]

            resolution = format_parts[0]
            height = int(resolution[:-len('p')])
            bitrate = int(format_parts[1][:-len('k')])
            format = '-'.join(format_parts) + '-' + dn

            formats.append({
                'url': video_url,
                'format': format,
                'format_id': format,
                'height': height,
                'tbr': bitrate,
                'resolution': resolution,
            })

        self._sort_formats(formats)

        if not formats:
            raise ExtractorError('ERROR: no known formats available for video')

        return {
            'id': video_id,
            'title': video_title,
            'age_limit': age_limit,
            'formats': formats,
        }
