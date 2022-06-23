# coding: utf-8
from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor
from ..compat import (
    compat_str,
)
from ..utils import (
    clean_html,
    get_element_by_class,
    sanitize_url,
    url_or_none,
    urljoin,
)


class ThisVidIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?thisvid\.com/(?P<type>videos|embed)/(?P<id>[A-Za-z0-9-]+/?)'
    _TESTS = [{
        'url': 'https://thisvid.com/videos/sitting-on-ball-tight-jeans/',
        'md5': '839becb572995687e11a69dc4358a386',
        'info_dict': {
            'id': '3533241',
            'ext': 'mp4',
            'title': 'Sitting on ball tight jeans',
            'thumbnail': r're:https?://\w+\.thisvid\.com/(?:[^/]+/)+3533241/preview\.jpg',
            'uploader_id': '150629',
            'uploader': 'jeanslevisjeans',
            'age_limit': 18,
        }
    }, {
        'url': 'https://thisvid.com/embed/3533241/',
        'md5': '839becb572995687e11a69dc4358a386',
        'info_dict': {
            'id': '3533241',
            'ext': 'mp4',
            'title': 'Sitting on ball tight jeans',
            'thumbnail': r're:https?://\w+\.thisvid\.com/(?:[^/]+/)+3533241/preview\.jpg',
            'uploader_id': '150629',
            'uploader': 'jeanslevisjeans',
            'age_limit': 18,
        }
    }]

    def _real_extract(self, url):
        main_id, type_ = re.match(self._VALID_URL, url).group('id', 'type')
        webpage = self._download_webpage(url, main_id)

        # URL decryptor was reversed from version 4.0.4, later verified working with 5.0.1
        kvs_version = self._html_search_regex(r'<script [^>]+?src="https://thisvid\.com/player/kt_player\.js\?v=(\d+(\.\d+)+)">', webpage, 'kvs_version', fatal=False)
        if not (kvs_version and kvs_version.startswith('5.')):
            self.report_warning('Major version change (' + kvs_version + ') in player engine--Download may fail.')

        title = self._html_search_regex(r'<title\b[^>]*?>(?:Video:\s+)?(.+?)(?:\s+-\s+ThisVid(?:\.com| tube))?</title>', webpage, 'title')
        video_holder = get_element_by_class('video-holder', webpage) or ''
       if '>This video is a private video' in video_holder:
           self.raise_login_required(
               (clean_html(video_holder) or 'Private video').split('\n', 1)[0])
       # video_id, video_url and license_code from the 'flashvars' JSON object:
        video_id = self._html_search_regex(r"video_id:\s+'([0-9]+)',", webpage, 'video_id')
        video_url = self._html_search_regex(r"video_url:\s+'function/0/((?:[^/']+/){5,}.+?)',", webpage, 'video_url')
        license_code = self._html_search_regex(r"license_code:\s+'([0-9$]{16})',", webpage, 'license_code')
        thumbnail = self._html_search_regex(r"preview_url:\s+'((?:https?:)?//media\.thisvid\.com/.+?\.jpg)',", webpage, 'thumbnail', fatal=False)
        uploader = self._html_search_regex(r'''(?s)<span\b[^>]*>Added by:\s*</span><a\b[^>]+\bclass\s*=\s*["']author\b[^>]+\bhref\s*=\s*["']https://thisvid\.com/members/([0-9]+/.{3,}?)\s*</a>''', webpage, 'uploader', default='')
        uploader = re.split(r'''/["'][^>]*>\s*''', uploader)
        if len(uploader) == 2:
            # id must be non-empty, uploader could be ''
            uploader_id, uploader = uploader
            uploader = uploader or None
        else:
            uploader_id = uploader = None
        thumbnail = sanitize_url(thumbnail)
        display_id = self._search_regex(r'<link\s+rel\s*=\s*"canonical"\s+href\s*=\s*"%s"' % (self._VALID_URL, ), webpage, 'display_id', fatal=False) if type_ == 'videos' else main_id

        return {
            'id': video_id,
            'display_id': main_id,
            'title': title,
            'url': getrealurl(video_url, license_code),
            'thumbnail': thumbnail,
            'age_limit': 18,
            'uploader': uploader,
            'uploader_id': uploader_id,
        }


def getrealurl(video_url, license_code):
    urlparts = video_url.split('/')
    license = getlicensetoken(license_code)
    newmagic = urlparts[5][:32]

    for o in range(len(newmagic) - 1, -1, -1):
        new = ''
        l = (o + sum([int(n) for n in license[o:]])) % 32

        for i in range(0, len(newmagic)):
            idx = i
            if idx == o:
                idx = l
            elif idx == l:
                idx = o
            new += newmagic[idx]
        newmagic = new

    urlparts[5] = newmagic + urlparts[5][32:]
    return "/".join(urlparts)


def getlicensetoken(license):
    modlicense = license.replace("$", "").replace("0", "1")
    center = len(modlicense) // 2
    fronthalf = int(modlicense[:center + 1])
    backhalf = int(modlicense[center:])

    modlicense = compat_str(4 * abs(fronthalf - backhalf))
    retval = ''
    for o in range(0, center + 1):
        for i in range(1, 5):
            retval += compat_str((int(license[o + i]) + int(modlicense[o])) % 10)
    return retval
