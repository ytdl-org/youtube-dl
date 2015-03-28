# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import urllib2
import xml.etree.ElementTree as ET
import re


class DHMIE(InfoExtractor):
    IE_DESC = 'Deutsches Historisches Museum'
    _VALID_URL = r'http://www\.dhm\.de/filmarchiv/(?P<id>.*?)'

    _TEST = {
        'url': 'http://www.dhm.de/filmarchiv/die-filme/the-marshallplan-at-work-in-west-germany/',
        'md5': '11c475f670209bf6acca0b2b7ef51827',
        'info_dict': {
            'id': 'marshallwg',
            'ext': 'flv',
            'title': 'MARSHALL PLAN AT WORK IN WESTERN GERMANY, THE',
            'thumbnail': 'http://www.dhm.de/filmarchiv/video/mpworkwg.jpg',
        }
    }

    def _real_extract(self, url):
        video_id = ''
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'dc:title=\"(.*?)\"', webpage, 'title')

        playlist_url = self._html_search_regex(
            r'file: \'(.*?)\'', webpage, 'playlist URL')

        xml_file = urllib2.urlopen(playlist_url)
        data = xml_file.read()
        xml_file.close()

        root = ET.fromstring(data)
        video_url = root[0][0][0].text
        thumbnail = root[0][0][2].text

        m = re.search('video/(.+?).flv', video_url)
        if m:
            video_id = m.group(1)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
        }
