from __future__ import unicode_literals

import re

from .common import InfoExtractor


class MusicVaultIE(InfoExtractor):
    _VALID_URL = r'https?://www\.musicvault\.com/(?P<uploader_id>[^/?#]*)/video/(?P<display_id>[^/?#]*)_(?P<id>[0-9]+)\.html'
    _TEST = {
        'url': 'http://www.musicvault.com/the-allman-brothers-band/video/straight-from-the-heart_1010863.html',
        'md5': '3adcbdb3dcc02d647539e53f284ba171',
        'info_dict': {
            'id': '1010863',
            'ext': 'mp4',
            'uploader_id': 'the-allman-brothers-band',
            'title': 'Straight from the Heart',
            'duration': 244,
            'uploader': 'The Allman Brothers Band',
            'thumbnail': 're:^https?://.*/thumbnail/.*',
            'upload_date': '20131219',
            'location': 'Capitol Theatre (Passaic, NJ)',
            'description': 'Listen to The Allman Brothers Band perform Straight from the Heart at Capitol Theatre (Passaic, NJ) on Dec 16, 1981',
            'timestamp': int,
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
        location = self._html_search_regex(
            r'<h4.*?>(.*?)</h4>', data_div, 'location', fatal=False)

        kaltura_id = self._search_regex(
            r'<div id="video-detail-player" data-kaltura-id="([^"]+)"',
            webpage, 'kaltura ID')
        wid = self._search_regex(r'/wid/_([0-9]+)/', webpage, 'wid')

        return {
            'id': mobj.group('id'),
            '_type': 'url_transparent',
            'url': 'kaltura:%s:%s' % (wid, kaltura_id),
            'ie_key': 'Kaltura',
            'display_id': display_id,
            'uploader_id': mobj.group('uploader_id'),
            'thumbnail': thumbnail,
            'description': self._html_search_meta('description', webpage),
            'location': location,
            'title': title,
            'uploader': uploader,
        }
