# coding: utf-8
from __future__ import unicode_literals

import os.path
import re

from ..compat import compat_urllib_parse_unquote
from ..utils import url_basename
from .common import InfoExtractor

class NprIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?npr\.org/player/v2/mediaPlayer.html?.*id=(?P<id>[0-9]+)'
    _TEST = {
    'url': 'http://www.npr.org/player/v2/mediaPlayer.html?id=445367719',
    'info_dict': {
        'id': '445367719',
        'ext': 'mp4',
        'title': 'VEGA INTL. Night School'
    }
}


    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage_url = 'http://www.npr.org/player/v2/mediaPlayer.html?id=' + video_id
        webpage = self._download_webpage(webpage_url, video_id)
        key = 'MDAzMzQ2MjAyMDEyMzk4MTU1MDg3ZmM3MQ010'
        xml_url = 'http://api.npr.org/query?id=%s&apiKey=%s' % (video_id, key)
        json_url = 'http://api.npr.org/query?id=%s&apiKey=%s&format=json' % (video_id, key)

        formats = []
        entries = []

        config = self._download_json(json_url, video_id)

        content = config["list"]["story"]

        album_title = config["list"]["story"][0]['song'][0]['album']['albumTitle']
        print album_title['$text']

        for key in content:
            if "audio" in key:
                for x in key['audio']:
                    if x['type'] == 'standard':
                        playlist = True
                        song_duration = x["duration"]['$text']
                        song_title = x["title"]["$text"]
                        song_id = x["id"]

                        for k in x["format"]:
                            if type(x["format"][k]) is list:
                                for z in x["format"][k]:
                                    formats.append({ 'format': z['type'], 
                                                     'url'   : z['$text']
                                              })
                            else:
                                formats.append({ 'format': k, 
                                                 'url'   : x["format"][k]['$text']
                                      })

                        entries.append({ "title":song_title,
                                         "id":song_id,
                                         "duration": song_duration ,
                                         "formats":formats})
                        formats = []

        return {    '_type': 'playlist',
                    'id' : video_id,
                    'title' : album_title,
                    'entries': entries  }
