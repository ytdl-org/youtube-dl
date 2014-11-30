from __future__ import unicode_literals

import re

from .common import InfoExtractor


class TeamcocoIE(InfoExtractor):
    _VALID_URL = r'http://teamcoco\.com/video/(?P<video_id>[0-9]+)?/?(?P<display_id>.*)'
    _TESTS = [
        {
            'url': 'http://teamcoco.com/video/80187/conan-becomes-a-mary-kay-beauty-consultant',
            'file': '80187.mp4',
            'md5': '3f7746aa0dc86de18df7539903d399ea',
            'info_dict': {
                'title': 'Conan Becomes A Mary Kay Beauty Consultant',
                'description': 'Mary Kay is perhaps the most trusted name in female beauty, so of course Conan is a natural choice to sell their products.'
            }
        }, {
            'url': 'http://teamcoco.com/video/louis-ck-interview-george-w-bush',
            'file': '19705.mp4',
            'md5': 'cde9ba0fa3506f5f017ce11ead928f9a',
            'info_dict': {
                "description": "Louis C.K. got starstruck by George W. Bush, so what? Part one.",
                "title": "Louis C.K. Interview Pt. 1 11/3/11"
            }
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        display_id = mobj.group('display_id')
        webpage = self._download_webpage(url, display_id)

        video_id = mobj.group("video_id")
        if not video_id:
            video_id = self._html_search_regex(
                r'data-node-id="(\d+?)"',
                webpage, 'video id')

        data_url = 'http://teamcoco.com/cvp/2.0/%s.xml' % video_id
        data = self._download_xml(
            data_url, display_id, 'Downloading data webpage')

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
            'display_id': display_id,
            'formats': formats,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
        }
