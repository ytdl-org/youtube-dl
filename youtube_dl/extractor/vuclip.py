from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlparse,
)
from ..utils import (
    ExtractorError,
    parse_duration,
    qualities,
)


class VuClipIE(InfoExtractor):
    _VALID_URL = r'https?://(?:m\.)?vuclip\.com/w\?.*?cid=(?P<id>[0-9]+)'

    _TEST = {
        'url': 'http://m.vuclip.com/w?cid=922692425&fid=70295&z=1010&nvar&frm=index.html',
        'info_dict': {
            'id': '922692425',
            'ext': '3gp',
            'title': 'The Toy Soldiers - Hollywood Movie Trailer',
            'duration': 180,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        ad_m = re.search(
            r'''value="No.*?" onClick="location.href='([^"']+)'"''', webpage)
        if ad_m:
            urlr = compat_urllib_parse_urlparse(url)
            adfree_url = urlr.scheme + '://' + urlr.netloc + ad_m.group(1)
            webpage = self._download_webpage(
                adfree_url, video_id, note='Download post-ad page')

        error_msg = self._html_search_regex(
            r'<p class="message">(.*?)</p>', webpage, 'error message',
            default=None)
        if error_msg:
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, error_msg), expected=True)

        # These clowns alternate between two page types
        links_code = self._search_regex(
            r'''(?xs)
                (?:
                    <img\s+src="[^"]*/play.gif".*?>|
                    <!--\ player\ end\ -->\s*</div><!--\ thumb\ end-->
                )
                (.*?)
                (?:
                    <a\s+href="fblike|<div\s+class="social">
                )
            ''', webpage, 'links')
        title = self._html_search_regex(
            r'<title>(.*?)-\s*Vuclip</title>', webpage, 'title').strip()

        quality_order = qualities(['Reg', 'Hi'])
        formats = []
        for url, q in re.findall(
                r'<a\s+href="(?P<url>[^"]+)".*?>(?:<button[^>]*>)?(?P<q>[^<]+)(?:</button>)?</a>', links_code):
            format_id = compat_urllib_parse_urlparse(url).scheme + '-' + q
            formats.append({
                'format_id': format_id,
                'url': url,
                'quality': quality_order(q),
            })
        self._sort_formats(formats)

        duration = parse_duration(self._search_regex(
            r'\(([0-9:]+)\)</span>', webpage, 'duration', fatal=False))

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'duration': duration,
        }
