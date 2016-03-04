# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote_plus
from ..utils import int_or_none


class KUSIIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?kusi\.com/(?P<path>story/.+|video\?clipId=(?P<clipId>\d+))'
    _TEST = {
        'url': 'http://www.kusi.com/story/31183873/turko-files-case-closed-put-on-hold',
        'md5': 'f926e7684294cf8cb7bdf8858e1b3988',
        'info_dict': {
            'id': '12203019',
            'ext': 'mp4',
            'title': 'Turko Files: Case Closed! & Put On Hold!',
            'duration': 231000,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        if mobj.group('clipId') is not None:
            video_id = mobj.group('clipId')
        else:
            webpage = self._download_webpage(url, mobj.group('path'))
            video_id = self._html_search_regex(r'"clipId", "(\d+)"', webpage,
                                               'clipId')

        xml_url = 'http://www.kusi.com/build.asp?buildtype=buildfeaturexml'\
                  'request&featureType=Clip&featureid={0}&affiliateno=956&'\
                  'clientgroupid=1&rnd=562461'.format(video_id)
        doc = self._download_xml(xml_url, video_id,
                                 note='Downloading video info',
                                 errnote='Failed to download video info')

        video_title = doc.find('HEADLINE').text
        duration = int_or_none(doc.find('DURATION'), get_attr='text')
        description = doc.find('ABSTRACT')

        quality_options = doc.find('{http://search.yahoo.com/mrss/}group').findall('{http://search.yahoo.com/mrss/}content')
        formats = []
        for quality in quality_options:
            if 'height' in quality.attrib:
                formats.append({
                    'url': compat_urllib_parse_unquote_plus(quality.attrib['url']),
                    'height': quality.attrib['height'],
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'description': description,
            'duration': duration,
            'formats': formats,
        }
