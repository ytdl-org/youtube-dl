from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse,
    parse_duration,
    qualities,
)


class VuClipIE(InfoExtractor):
    _VALID_URL = r'http://(?:m\.)?vuclip\.com/w\?.*?cid=(?P<id>[0-9]+)'

    _TEST = {
        'url': 'http://m.vuclip.com/w?cid=843902317&fid=63532&z=1007&nvar&frm=index.html&bu=4757321434',
        'md5': '92ac9d1ccefec4f0bb474661ab144fcf',
        'info_dict': {
            'id': '843902317',
            'ext': '3gp',
            'title': 'Movie Trailer: Noah',
            'duration': 139,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        ad_m = re.search(
            r'''value="No.*?" onClick="location.href='([^"']+)'"''', webpage)
        if ad_m:
            urlr = compat_urllib_parse_urlparse(url)
            adfree_url = urlr.scheme + '://' + urlr.netloc + ad_m.group(1)
            webpage = self._download_webpage(
                adfree_url, video_id, note='Download post-ad page')

        links_code = self._search_regex(
            r'(?s)<div class="social align_c".*?>(.*?)<hr\s*/?>', webpage,
            'links')
        title = self._html_search_regex(
            r'<title>(.*?)-\s*Vuclip</title>', webpage, 'title').strip()

        quality_order = qualities(['Reg', 'Hi'])
        formats = []
        for url, q in re.findall(
                r'<a href="(?P<url>[^"]+)".*?>(?P<q>[^<]+)</a>', links_code):
            format_id = compat_urllib_parse_urlparse(url).scheme + '-' + q
            formats.append({
                'format_id': format_id,
                'url': url,
                'quality': quality_order(q),
            })
        self._sort_formats(formats)

        duration = parse_duration(self._search_regex(
            r'\(([0-9:]+)\)</span></h1>', webpage, 'duration', fatal=False))

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'duration': duration,
        }
