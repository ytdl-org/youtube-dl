# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re


class ToypicsIE(InfoExtractor):
    IE_DESC = 'Toypics user profile'
    _VALID_URL = r'https?://videos\.toypics\.net/view/(?P<id>[0-9]+)/.*'
    _TEST = {
        'url': 'http://videos.toypics.net/view/514/chancebulged,-2-1/',
        'md5': '16e806ad6d6f58079d210fe30985e08b',
        'info_dict': {
            'id': '514',
            'ext': 'mp4',
            'title': 'Chance-Bulge\'d, 2',
            'age_limit': 18,
            'uploader': 'kidsune',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        page = self._download_webpage(url, video_id)
        video_url = self._html_search_regex(
            r'src:\s+"(http://static[0-9]+\.toypics\.net/flvideo/[^"]+)"', page, 'video URL')
        title = self._html_search_regex(
            r'<title>Toypics - ([^<]+)</title>', page, 'title')
        username = self._html_search_regex(
            r'toypics.net/([^/"]+)" class="user-name">', page, 'username')
        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'uploader': username,
            'age_limit': 18,
        }


class ToypicsUserIE(InfoExtractor):
    IE_DESC = 'Toypics user profile'
    _VALID_URL = r'https?://videos\.toypics\.net/(?P<username>[^/?]+)(?:$|[?#])'
    _TEST = {
        'url': 'http://videos.toypics.net/Mikey',
        'info_dict': {
            'id': 'Mikey',
        },
        'playlist_mincount': 19,
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        username = mobj.group('username')

        profile_page = self._download_webpage(
            url, username, note='Retrieving profile page')

        video_count = int(self._search_regex(
            r'public/">Public Videos \(([0-9]+)\)</a></li>', profile_page,
            'video count'))

        PAGE_SIZE = 8
        urls = []
        page_count = (video_count + PAGE_SIZE + 1) // PAGE_SIZE
        for n in range(1, page_count + 1):
            lpage_url = url + '/public/%d' % n
            lpage = self._download_webpage(
                lpage_url, username,
                note='Downloading page %d/%d' % (n, page_count))
            urls.extend(
                re.findall(
                    r'<p class="video-entry-title">\s+<a href="(https?://videos.toypics.net/view/[^"]+)">',
                    lpage))

        return {
            '_type': 'playlist',
            'id': username,
            'entries': [{
                '_type': 'url',
                'url': eurl,
                'ie_key': 'Toypics',
            } for eurl in urls]
        }
