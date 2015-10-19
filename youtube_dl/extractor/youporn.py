from __future__ import unicode_literals


import json
import re
import sys
import datetime

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
            'description': 'Watch Sex Ed: Is It Safe To Masturbate Daily? at YouPorn.com - YouPorn is the biggest free porn tube site on the net!',
            'uploader': 'Ask Dan And Jennifer',
            'thumbnail': 'http://cdn5.image.youporn.phncdn.com/201012/17/505835/640x480/8/sex-ed-is-it-safe-to-masturbate-daily-8.jpg',
            'date': '20101221',
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
        video_title = self._html_search_regex(r'page_params.video_title = \'(.+?)\';', webpage, 'video URL', fatal=False)
        video_description = self._html_search_meta('description', webpage, 'video DESC', fatal=False)
        video_thumbnail = self._html_search_regex(r'page_params.imageurl\t=\t"(.+?)";', webpage, 'video THUMB', fatal=False)
        video_uploader = self._html_search_regex(r"<div class=\'videoInfoBy\'>By:</div>\n<a href=\"[^>]+\">(.+?)</a>", webpage, 'video UPLOADER', fatal=False)
        video_date = self._html_search_regex(r"<div class='videoInfoTime'>\n<i class='icon-clock'></i> (.+?)\n</div>", webpage, 'video DATE', fatal=False)
        video_date = datetime.datetime.strptime(video_date, '%B %d, %Y').strftime('%Y%m%d')

        # Get all of the links from the page
        DOWNLOAD_LIST_RE = r'(?s)sources: {\n(?P<testje>.*?)}'
        download_list_html = self._search_regex(DOWNLOAD_LIST_RE, webpage, 'testje').strip()
        LINK_RE = r': \'(.+?)\','
        links = re.findall(LINK_RE, download_list_html)

        formats = []
        for link in links:

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
            'description': video_description,
            'thumbnail': video_thumbnail,
            'uploader': video_uploader,
            'date': video_date,
            'age_limit': age_limit,
            'formats': formats,
        }
