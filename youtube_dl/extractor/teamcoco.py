from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class TeamcocoIE(InfoExtractor):
    _VALID_URL = r'http://teamcoco\.com/video/(?P<url_title>.*)'
    _TEST = {
        'url': 'http://teamcoco.com/video/louis-ck-interview-george-w-bush',
        'file': '19705.mp4',
        'md5': 'cde9ba0fa3506f5f017ce11ead928f9a',
        'info_dict': {
            "description": "Louis C.K. got starstruck by George W. Bush, so what? Part one.",
            "title": "Louis C.K. Interview Pt. 1 11/3/11"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError('Invalid URL: %s' % url)
        url_title = mobj.group('url_title')
        webpage = self._download_webpage(url, url_title)

        video_id = self._html_search_regex(
            r'<article class="video" data-id="(\d+?)"',
            webpage, 'video id')

        self.report_extraction(video_id)

        data_url = 'http://teamcoco.com/cvp/2.0/%s.xml' % video_id
        data = self._download_xml(data_url, video_id, 'Downloading data webpage')

        qualities = ['500k', '480p', '1000k', '720p', '1080p']
        formats = []
        for filed in data.findall('files/file'):
            if filed.attrib.get('playmode') == 'all':
                # it just duplicates one of the entries
                break
            file_url = filed.text
            m_format = re.search(r'(\d+(k|p))\.mp4', file_url)
            if m_format is not None:
                format_id = m_format.group(1)
            else:
                format_id = filed.attrib['bitrate']
            tbr = (
                int(filed.attrib['bitrate'])
                if filed.attrib['bitrate'].isdigit()
                else None)

            try:
                quality = qualities.index(format_id)
            except ValueError:
                quality = -1
            formats.append({
                'url': file_url,
                'ext': 'mp4',
                'tbr': tbr,
                'format_id': format_id,
                'quality': quality,
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
        }
