from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_duration,
)


class VideoLecturesNetIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?videolectures\.net/(?P<id>[^/#?]+)/*(?:[#?].*)?$'
    IE_NAME = 'videolectures.net'

    _TEST = {
        'url': 'http://videolectures.net/promogram_igor_mekjavic_eng/',
        'info_dict': {
            'id': 'promogram_igor_mekjavic_eng',
            'ext': 'mp4',
            'title': 'Automatics, robotics and biocybernetics',
            'description': 'md5:815fc1deb6b3a2bff99de2d5325be482',
            'upload_date': '20130627',
            'duration': 565,
            'thumbnail': 're:http://.*\.jpg',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        smil_url = 'http://videolectures.net/%s/video/1/smil.xml' % video_id
        smil = self._download_smil(smil_url, video_id)

        info = self._parse_smil(smil, smil_url, video_id)

        info['id'] = video_id

        switch = smil.find('.//switch')
        if switch is not None:
            info['duration'] = parse_duration(switch.attrib.get('dur'))

        return info
