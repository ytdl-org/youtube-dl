# coding: utf-8

from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor


class JeuxVideoIE(InfoExtractor):
    _VALID_URL = r'http://.*?\.jeuxvideo\.com/.*/(.*?)-\d+\.htm'

    _TEST = {
        'url': 'http://www.jeuxvideo.com/reportages-videos-jeux/0004/00046170/tearaway-playstation-vita-gc-2013-tearaway-nous-presente-ses-papiers-d-identite-00115182.htm',
        'md5': '046e491afb32a8aaac1f44dd4ddd54ee',
        'info_dict': {
            'id': '5182',
            'ext': 'mp4',
            'title': 'GC 2013 : Tearaway nous présente ses papiers d\'identité',
            'description': 'Lorsque les développeurs de LittleBigPlanet proposent un nouveau titre, on ne peut que s\'attendre à un résultat original et fort attrayant.\n',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title = mobj.group(1)
        webpage = self._download_webpage(url, title)
        xml_link = self._html_search_regex(
            r'<param name="flashvars" value="config=(.*?)" />',
            webpage, 'config URL')

        video_id = self._search_regex(
            r'http://www\.jeuxvideo\.com/config/\w+/\d+/(.*?)/\d+_player\.xml',
            xml_link, 'video ID')

        config = self._download_xml(
            xml_link, title, 'Downloading XML config')
        info_json = config.find('format.json').text
        info = json.loads(info_json)['versions'][0]

        video_url = 'http://video720.jeuxvideo.com/' + info['file']

        return {
            'id': video_id,
            'title': config.find('titre_video').text,
            'ext': 'mp4',
            'url': video_url,
            'description': self._og_search_description(webpage),
            'thumbnail': config.find('image').text,
        }
