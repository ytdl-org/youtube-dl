# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor
from ..utils import str_to_int


class PressTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?presstv\.ir/Video/(?P<y>[0-9]+)/(?P<m>[0-9]+)/(?P<d>[0-9]+)/(?P<id>[0-9]+)/'

    _TEST = {
        'url': 'http://www.presstv.ir/Video/2015/10/04/431915/Max-Igan-Press-TV-Face-to-Face',
        'md5': 'e95736ac75088b5f1e5bbb68f248f90d',
        'info_dict': {
            'id': '431915',
            'ext': 'mp4',
            'title': 'Press TV’s full interview with Max Igan',
            'upload_date': '20151004',
            'thumbnail': 'http://217.218.67.233/photo/20151004/d5c333ad-98f9-4bd3-bc3e-a1ad6a192803.jpg',
            'description': ('Watch Press TV’s full interview with Max Igan, a radio talk show host and political '
                            'commentator.\nThe interview, conducted on Press TV’s Face '
                            'to Face program, was aired on October 3, 2015.')
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
        title = title.partition(' - ')[2]

        description = self._html_search_regex(r'<div class="media-text nano-content">(.*?)</div>', webpage,
                                              'Description', flags=re.DOTALL)

        thumbnail = self._html_search_meta('og:image', webpage, 'Thumbnail', True)

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
