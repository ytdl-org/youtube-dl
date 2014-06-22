# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    qualities,
    determine_ext,
)


class TeacherTubeIE(InfoExtractor):
    IE_NAME = 'teachertube'
    IE_DESC = 'teachertube.com videos'

    _VALID_URL = r'https?://(?:www\.)?teachertube\.com/(viewVideo\.php\?video_id=|music\.php\?music_id=)(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.teachertube.com/viewVideo.php?video_id=339997',
        'md5': 'f9434ef992fd65936d72999951ee254c',
        'info_dict': {
            'id': '339997',
            'ext': 'mp4',
            'title': 'Measures of dispersion from a frequency table',
            'description': 'Measures of dispersion from a frequency table',
            'thumbnail': 're:http://.*\.jpg',
        },
    }, {
        'url': 'http://www.teachertube.com/viewVideo.php?video_id=340064',
        'md5': '0d625ec6bc9bf50f70170942ad580676',
        'info_dict': {
            'id': '340064',
            'ext': 'mp4',
            'title': 'How to Make Paper Dolls _ Paper Art Projects',
            'description': 'Learn how to make paper dolls in this simple',
            'thumbnail': 're:http://.*\.jpg',
        },
    }, {
        'url': 'http://www.teachertube.com/music.php?music_id=8805',
        'md5': '01e8352006c65757caf7b961f6050e21',
        'info_dict': {
            'id': '8805',
            'ext': 'mp3',
            'title': 'PER ASPERA AD ASTRA',
            'description': 'RADIJSKA EMISIJA ZRAKOPLOVNE TEHNI?KE ?KOLE P',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_meta('title', webpage, 'title')
        TITLE_SUFFIX = ' - TeacherTube'
        if title.endswith(TITLE_SUFFIX):
            title = title[:-len(TITLE_SUFFIX)].strip()

        description = self._html_search_meta('description', webpage, 'description')
        if description:
            description = description.strip()

        quality = qualities(['mp3', 'flv', 'mp4'])

        media_urls = re.findall(r'data-contenturl="([^"]+)"', webpage)
        media_urls.extend(re.findall(r'var\s+filePath\s*=\s*"([^"]+)"', webpage))

        formats = [
            {
                'url': media_url,
                'quality': quality(determine_ext(media_url))
            } for media_url in set(media_urls)
        ]

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': self._html_search_regex(r'var\s+thumbUrl\s*=\s*"([^"]+)"', webpage, 'thumbnail'),
            'formats': formats,
            'description': description,
        }


class TeacherTubeClassroomIE(InfoExtractor):
    IE_NAME = 'teachertube:classroom'
    IE_DESC = 'teachertube.com online classrooms'

    _VALID_URL = r'https?://(?:www\.)?teachertube\.com/view_classroom\.php\?user=(?P<user>[0-9a-zA-Z]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user_id = mobj.group('user')

        rss = self._download_xml(
            'http://www.teachertube.com/rssclassroom.php?mode=user&username=%s' % user_id,
            user_id, 'Downloading classroom RSS')

        entries = []
        for url in rss.findall('.//{http://search.yahoo.com/mrss/}player'):
            entries.append(self.url_result(url.attrib['url'], 'TeacherTube'))

        return self.playlist_result(entries, user_id)
