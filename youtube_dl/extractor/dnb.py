# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re
import json


class DNBIE(InfoExtractor):
    _VALID_URL = r'https?://(?:portal\.dnb\.de/audioplayer/do/show/|d-nb\.info/)(?P<id>\w+)[/&]?'
    _TESTS = [{
        'url': 'https://portal.dnb.de/audioplayer/do/show/1077188552#dcId=1546432571580&p=1',
        'md5': 'cdef1faf339db9978b27c70ef4c0516b',
        'info_dict': {
            'title': 'Leonoren-Ouvertüre III [Elektronische Ressource] : Allegro / Ludwig van Beethoven (1770-1827)',
            'id': '1077188552',
            'ext': 'mp3',
            'track': 'Track 1',
            'track_number': 1
        }
    }, {
        'url': 'http://d-nb.info/1077188552',
        'md5': 'cdef1faf339db9978b27c70ef4c0516b',
        'info_dict': {
            'title': 'Leonoren-Ouvertüre III [Elektronische Ressource] : Allegro / Ludwig van Beethoven (1770-1827)',
            'id': '1077188552',
            'ext': 'mp3',
            'track': 'Track 1',
            'track_number': 1
        }
    }]

    @staticmethod
    def update_and_return_dic(info_dict, update_info):
        ret = info_dict.copy()
        ret.update(update_info)
        return ret

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'https://portal.dnb.de/audioplayer/do/show/' + video_id
        webpage = self._download_webpage(url, video_id)

        m = re.search(r'fdnbpl.media\s*=\s*(\[.*\]);', webpage)
        objs = json.loads(m.group(1))

        result = []
        num = 1
        for obj in objs:
            thumbnail = obj.get('cover_url')
            if thumbnail:
                thumbnail = 'https://portal.dnb.de/' + thumbnail

            info_dict = {
                'id': obj.get('idn'),
                'title': obj.get('title'),
                'author': obj.get('author'),
                'url': 'https://portal.dnb.de/' + obj.get('media_url'),
                'ext': 'mp3',
                'thumbnail': thumbnail
            }

            tracks = [type(self).update_and_return_dic(info_dict,
                                                       {
                                                           'track': ti[1].get('title'),
                                                           'track_number': ti[0]
                                                       })
                      for ti in enumerate(obj.get('tracks'), start=num)]
            result.extend(tracks)
            num += len(tracks)

        return {
            '_type': 'playlist',
            'entries': result
        }
