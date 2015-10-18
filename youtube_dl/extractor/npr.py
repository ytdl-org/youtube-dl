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

        config = self._download_xml(xml_url,video_id, note='Downloading XML')

        audio = config.findall('./list/story/audio[@type="standard"]')
        if not audio:
            # audio type is primary
            audio = config.findall('./list/story/audio[@type="primary"]')

        regex = ('.//*[@type="mp3"]','.//*[@type="m3u"]','.//format/wm','.//format/threegp','.//format/mp4','.//format/hls','.//format/mediastream')
        album_title = config.find('.//albumTitle')

        if not album_title:
            album_title = config.find('./list/story/title').text
        else:
            album_title = album_title.text

        print(album_title)
        format = []
        entries = []
        for song in audio:
            song_title = song.find('title').text
            song_id = song.get('id')
            song_duration = song.find('duration').text

            for r in regex:
                t = song.find(r)
                if t is not None:
                    format.append({'format': t.get('type', t.tag),
                               'url' : t.text})

            entries.append({ "title":song_title,
                             "id":song_id,
                             "duration": str(int(song_duration) / 60) +":"+ str(int(song_duration) % 60) ,
                             "formats":format})
            format = []

        return {
            '_type': 'playlist',
            'id' : video_id,
            'title' : album_title,
            'entries': entries
        }