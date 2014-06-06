# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class TeacherTubeIE(InfoExtractor):
    IE_NAME = 'teachertube'
    IE_DESC = 'teachertube.com videos'

    _VALID_URL = r'https?://(?:www\.)?teachertube\.com/viewVideo\.php\?video_id=(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.teachertube.com/viewVideo.php?video_id=339997',
        'md5': 'f9434ef992fd65936d72999951ee254c',
        'info_dict': {
            'id': '339997',
            'ext': 'mp4',
            'title': 'Measures of dispersion from a frequency table_x264',
            'description': 'md5:a3e9853487185e9fcd7181a07164650b',
            'thumbnail': 're:http://.*\.jpg',
        },
    }, {
        'url': 'http://www.teachertube.com/viewVideo.php?video_id=340064',
        'md5': '0d625ec6bc9bf50f70170942ad580676',
        'info_dict': {
            'id': '340064',
            'ext': 'mp4',
            'title': 'How to Make Paper Dolls _ Paper Art Projects',
            'description': 'md5:2ca52b20cd727773d1dc418b3d6bd07b',
            'thumbnail': 're:http://.*\.jpg',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        url = self._html_search_meta('twitter:player:stream', webpage, 'twitter player')

        formats = [{
            'format_id': 'flv',
            'url': url.replace('mp4v', 'flv').replace('.mp4', '.flv'),
            'quality': 0,
            'ext': 'flv',
        }, {
            'format_id': 'mp4',
            'url': url,
            'quality': 1,
            'ext': 'mp4',
        }]

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
        }


class TeacherTubeClassroomIE(InfoExtractor):
    IE_NAME = 'teachertube:classroom'
    IE_DESC = 'teachertube.com online classrooms'

    _VALID_URL = r'https?://(?:www\.)?teachertube\.com/view_classroom\.php\?user=(?P<user>[0-9a-zA-Z]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user_id = mobj.group('user')

        rss = self._download_xml('http://www.teachertube.com/rssclassroom.php?mode=user&username=%s' % user_id,
                                      user_id, 'Downloading classroom RSS')

        entries = []
        for url in rss.findall('.//{http://search.yahoo.com/mrss/}player'):
            entries.append(self.url_result(url.attrib['url'], 'TeacherTube'))

        return self.playlist_result(entries, user_id)
