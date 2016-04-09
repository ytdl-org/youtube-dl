# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor
from ..utils import str_to_int


class PressTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?presstv\.ir/[^/]+/(?P<y>[0-9]+)/(?P<m>[0-9]+)/(?P<d>[0-9]+)/(?P<id>[0-9]+)/'

    _TEST = {
        'url': 'http://www.presstv.ir/Detail/2016/04/09/459911/Australian-sewerage-treatment-facility-/',
        'md5': '5d7e3195a447cb13e9267e931d8dd5a5',
        'info_dict': {
            'id': '459911',
            'ext': 'mp4',
            'title': 'Organic mattresses used to clean waste water',
            'upload_date': '20160409',
            'thumbnail': 'http://media.presstv.com/photo/20160409/41719129-76fa-4372-a09d-bf348278eb5d.jpg',
            'description': ('A trial program at an Australian sewerage treatment facility hopes to change '
                            'the way waste water is treated by using plant mattresses to reduce chemical '
                            'and electricity use.')
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # extract video URL from webpage
        video_url = self._html_search_regex(r'<input type="hidden" id="inpPlayback" value="([^"]+)" />', webpage,
                                            'Video URL')

        # build list of available formats
        # specified in http://www.presstv.ir/Scripts/playback.js
        base_url = 'http://192.99.219.222:82/presstv'
        formats = [
            {
                'url': base_url + video_url,
                'format': '1080p mp4',
                'format_id': '1080p'
            }, {
                'url': base_url + video_url.replace(".mp4", "_low800.mp4"),
                'format': '720p mp4',
                'format_id': '720p'
            }, {
                'url': base_url + video_url.replace(".mp4", "_low400.mp4"),
                'format': '360p mp4',
                'format_id': '360p'
            }, {
                'url': base_url + video_url.replace(".mp4", "_low200.mp4"),
                'format': '180p mp4',
                'format_id': '180p'
            }
        ]
        formats.reverse()

        # extract video metadata
        title = self._html_search_meta('title', webpage, 'Title', True)
        title = title.partition('-')[2].strip()

        thumbnail = self._html_search_meta('og:image', webpage, 'Thumbnail', True)
        description = self._html_search_meta('og:description', webpage, 'Description', True)

        year = str_to_int(self._search_regex(PressTVIE._VALID_URL, url, 'Upload year', group='y'))
        month = str_to_int(self._search_regex(PressTVIE._VALID_URL, url, 'Upload month', group='m'))
        day = str_to_int(self._search_regex(PressTVIE._VALID_URL, url, 'Upload day', group='d'))
        upload_date = '%04d%02d%02d' % (year, month, day)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'description': description
        }
