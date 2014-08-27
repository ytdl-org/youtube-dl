from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    unified_strdate,
)


class MusicVaultIE(InfoExtractor):
    _VALID_URL = r'https?://www\.musicvault\.com/(?P<uploader_id>[^/?#]*)/video/(?P<display_id>[^/?#]*)_(?P<id>[0-9]+)\.html'
    _TEST = {
        'url': 'http://www.musicvault.com/the-allman-brothers-band/video/straight-from-the-heart_1010863.html',
        'md5': '2cdbb3ae75f7fb3519821507d2fb3c15',
        'info_dict': {
            'id': '1010863',
            'ext': 'mp4',
            'uploader_id': 'the-allman-brothers-band',
            'title': 'Straight from the Heart',
            'duration': 244,
            'uploader': 'The Allman Brothers Band',
            'thumbnail': 're:^https?://.*/thumbnail/.*',
            'upload_date': '19811216',
            'location': 'Capitol Theatre (Passaic, NJ)',
            'description': 'Listen to The Allman Brothers Band perform Straight from the Heart at Capitol Theatre (Passaic, NJ) on Dec 16, 1981',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')
        webpage = self._download_webpage(url, display_id)

        thumbnail = self._search_regex(
            r'<meta itemprop="thumbnail" content="([^"]+)"',
            webpage, 'thumbnail', fatal=False)

        data_div = self._search_regex(
            r'(?s)<div class="data">(.*?)</div>', webpage, 'data fields')
        uploader = self._html_search_regex(
            r'<h1.*?>(.*?)</h1>', data_div, 'uploader', fatal=False)
        title = self._html_search_regex(
            r'<h2.*?>(.*?)</h2>', data_div, 'title')
        upload_date = unified_strdate(self._html_search_regex(
            r'<h3.*?>(.*?)</h3>', data_div, 'uploader', fatal=False))
        location = self._html_search_regex(
            r'<h4.*?>(.*?)</h4>', data_div, 'location', fatal=False)

        duration = parse_duration(self._html_search_meta('duration', webpage))

        VIDEO_URL_TEMPLATE = 'http://cdnapi.kaltura.com/p/%(uid)s/sp/%(wid)s/playManifest/entryId/%(entry_id)s/format/url/protocol/http'
        kaltura_id = self._search_regex(
            r'<div id="video-detail-player" data-kaltura-id="([^"]+)"',
            webpage, 'kaltura ID')
        video_url = VIDEO_URL_TEMPLATE % {
            'entry_id': kaltura_id,
            'wid': self._search_regex(r'/wid/_([0-9]+)/', webpage, 'wid'),
            'uid': self._search_regex(r'uiconf_id/([0-9]+)/', webpage, 'uid'),
        }

        return {
            'id': mobj.group('id'),
            'url': video_url,
            'ext': 'mp4',
            'display_id': display_id,
            'uploader_id': mobj.group('uploader_id'),
            'thumbnail': thumbnail,
            'description': self._html_search_meta('description', webpage),
            'upload_date': upload_date,
            'location': location,
            'title': title,
            'uploader': uploader,
            'duration': duration,
        }
