# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor

import datetime
import time
import re

class PodlovePublisherIE(InfoExtractor):
    _VALID_URL = r'''(?:https?:)?//.+?/?podlove_action=pwp4_config'''

    _TEST = {
        'url': 'https://not-safe-for-work.de/nsfw099-kanzlerkind-sebastian/?podlove_action=pwp4_config',
        'md5': '73ab53f3898e752f6db89b50c3b4658c',
        'info_dict': {
            'id': 'NSFW099 Kanzlerkind Sebastian',
            'ext': 'm4a',
            'title': 'NSFW099 Kanzlerkind Sebastian',
            'description': 'Uuuuund da sind wir wieder, keine 10 Monate nachdem wir das letzte Mal gesendet haben. Und bedenkt, dass solche Sendezyklen im Kern gut für Euch sind. So oder so haben wir uns einiges zu erzählen, auch wenn wir zunehmend aus der alten Brachialität rauszuwachsen scheinen. Dafür mehr Blick in die Zeit und dann und wann auch ins Internet.',
            'duration': 11723
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(r'(?:https?:)?//.+?/?podlove_action=pwp4_config',webpage)
        if mobj:
            return mobj.group(0)
        else:
			return None

    def _real_extract(self, url):
        player_data = self._download_json(url, None)
        
        dur_ptime = time.strptime(player_data['duration'].split('.')[0],'%H:%M:%S')
        duration_secs = datetime.timedelta(hours=dur_ptime.tm_hour,minutes=dur_ptime.tm_min,seconds=dur_ptime.tm_sec).total_seconds()

        print(duration_secs)

        return {
            'id': player_data['title'],
            'title': player_data['title'],
            'description': player_data['summary'],
            'filesize': int(player_data['audio'][0]['size']),
            'url': player_data['audio'][0]['url'],
            'duration': duration_secs
            # TODO more properties (see youtube_dl/extractor/common.py)
        }






