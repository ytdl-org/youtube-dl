# coding: utf-8
from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urlparse,
)
from ..utils import (
    clean_html,
    get_element_by_class,
    int_or_none,
    sanitize_url,
    url_or_none,
    urljoin,
)


class ThisVidIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?thisvid\.com/(?P<type>videos|embed)/(?P<id>[A-Za-z0-9-]+)'
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

        title = self._html_search_regex(r'<title\b[^>]*?>(?:Video:\s+)?(.+?)(?:\s+-\s+ThisVid(?:\.com| tube))?</title>', webpage, 'title')
        if type_ == 'embed':
            video_alt_url = url_or_none(self._html_search_regex(r'''video_alt_url:\s+'(%s)',''' % (self._VALID_URL, ), webpage, 'video_alt_url', default=None))
            if video_alt_url:
                webpage = self._download_webpage(video_alt_url, main_id, note='Redirecting embed to main page', fatal=False)
        video_holder = get_element_by_class('video-holder', webpage) or ''
        if '>This video is a private video' in video_holder:
            self.raise_login_required(
                (clean_html(video_holder) or 'Private video').split('\n', 1)[0])

        # URL decryptor was reversed from version 4.0.4, later verified working with 5.0.1
        kvs_version = self._html_search_regex(r'<script [^>]+?src="https://thisvid\.com/player/kt_player\.js\?v=(\d+(\.\d+)+)">', webpage, 'kvs_version', fatal=False)
        if not (kvs_version and kvs_version.startswith('5.')):
            self.report_warning('Major version change (' + kvs_version + ') in player engine--Download may fail.')

        # video_id, video_url and license_code from the 'flashvars' JSON object:
        video_id = self._html_search_regex(r'''video_id:\s+'([0-9]+)',''', webpage, 'video_id')
        video_url = self._html_search_regex(r'''video_url:\s+'function/0/(https?://(?:[^/']+/){5,}.*?)',''', webpage, 'video_url')
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
            return '/'.join(urlparts)

        def getlicensetoken(license):
            modlicense = license.replace('$', '').replace('0', '1')
            center = len(modlicense) // 2
            fronthalf = int(modlicense[:center + 1])
            backhalf = int(modlicense[center:])

            modlicense = compat_str(4 * abs(fronthalf - backhalf))
            retval = ''
            for o in range(0, center + 1):
                for i in range(1, 5):
                    retval += compat_str((int(license[o + i]) + int(modlicense[o])) % 10)
            return retval

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


class ThisVidMemberIE(InfoExtractor):
    _VALID_URL = r'https?://thisvid\.com/members/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://thisvid.com/members/3235959/',
        'info_dict': {
            'id': '3235959',
            'title': 'ButtLoverAss\'s Profile',
        },
        'playlist_mincount': 64,
    }, {
        'url': 'https://thisvid.com/members/3235959/favourite_videos/',
        'info_dict': {
            'id': '3235959',
            'title': 'ButtLoverAss\'s Favourite Videos',
        },
        'playlist_mincount': 57,
    }, {
        'url': 'https://thisvid.com/members/3235959/public_videos/',
        'info_dict': {
            'id': '3235959',
            'title': 'ButtLoverAss\'s Public Videos',
        },
        'playlist_mincount': 29,
    },
    ]

    def _real_extract(self, url):
        pl_id = self._match_id(url)
        webpage = self._download_webpage(url, pl_id)

        title = re.split(
            r'(?i)\s*\|\s*ThisVid\.com\s*$',
            self._og_search_title(webpage, default=None) or self._html_search_regex(r'(?s)<title\b[^>]*>(.+?)</title', webpage, 'title', fatal=False) or '', 1)[0] or None

        def entries(page_url, html=None):
            for page in itertools.count(1):
                if not html:
                    html = self._download_webpage(
                        page_url, pl_id, note='Downloading page %d' % (page, ),
                        fatal=False) or ''
                for m in re.finditer(r'''<a\b[^>]+\bhref\s*=\s*["'](?P<url>%s\b)[^>]+>''' % (ThisVidIE._VALID_URL, ), html):
                    yield m.group('url')
                next_page = get_element_by_class('pagination-next', html)
                if next_page:
                    # member list page
                    next_page = urljoin(url, self._search_regex(
                        r'''<a\b[^>]+\bhref\s*=\s*("|')(?P<url>(?:(?!\1).)+)''',
                        next_page, 'next page link', group='url', default=None))
                # in case a member page should have pagination-next with empty link, not just `else:`
                if next_page is None:
                    # playlist page
                    parsed_url = compat_urlparse.urlparse(page_url)
                    base_path, num = parsed_url.path.rsplit('/', 1)
                    num = int_or_none(num)
                    if num is None:
                        base_path, num = parsed_url.path.rstrip('/'), 1
                    parsed_url._replace(path=base_path + ('/%d' % (num + 1, )))
                    next_page = compat_urlparse.urlunparse(parsed_url)
                    if page_url == next_page:
                        next_page = None
                if not next_page:
                    break
                page_url, html = next_page, None

        return self.playlist_from_matches(
            entries(url, webpage), playlist_id=pl_id, playlist_title=title, ie='ThisVid')


class ThisVidPlaylistIE(ThisVidMemberIE):
    _VALID_URL = r'https?://thisvid\.com/playlist/(?P<id>\d+)/video/(?P<video_id>[A-Za-z0-9-]+)'
    _TESTS = [{
        'url': 'https://thisvid.com/playlist/6615/video/big-italian-booty-28/',
        'info_dict': {
            'id': '6615',
            'title': 'Underwear Stuff',
        },
        'playlist_mincount': 207,
    }, {
        'url': 'https://thisvid.com/playlist/6615/video/big-italian-booty-28/',
        'info_dict': {
            'id': '1072387',
            'ext': 'mp4',
            'title': 'Big Italian Booty 28',
        },
        'params': {
            'noplaylist': True,
        },
    }]

    def _real_extract(self, url):
        pl_id, video_id = re.match(self._VALID_URL, url).groups('id', 'video_id')

        if self._downloader.params.get('noplaylist'):
            self.to_screen('Downloading just the featured video because of --no-playlist')
            return self.url_result(urljoin(url, '/videos/' + video_id), 'ThisVid', video_id)

        self.to_screen(
            'Downloading playlist {pl_id} - add --no-playlist to download just the featured video').format(locals())
        result = super(ThisVidPlaylistIE, self)._real_extract(url)

        # rework title returned as `the title - the title`
        title = result['title']
        t_len = len(title)
        if t_len > 5 and t_len % 2 != 0:
            t_len = t_len // 2
            if title[t_len] == '-' and title[:t_len] == title[t_len + 1:]:
                result['title'] = title[:t_len]
        return result
