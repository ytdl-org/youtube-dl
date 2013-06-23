import itertools
import json
import random
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class EightTracksIE(InfoExtractor):
    IE_NAME = '8tracks'
    _VALID_URL = r'https?://8tracks.com/(?P<user>[^/]+)/(?P<id>[^/#]+)(?:#.*)?$'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        playlist_id = mobj.group('id')

        webpage = self._download_webpage(url, playlist_id)

        json_like = self._search_regex(r"PAGE.mix = (.*?);\n", webpage, u'trax information', flags=re.DOTALL)
        data = json.loads(json_like)

        session = str(random.randint(0, 1000000000))
        mix_id = data['id']
        track_count = data['tracks_count']
        first_url = 'http://8tracks.com/sets/%s/play?player=sm&mix_id=%s&format=jsonh' % (session, mix_id)
        next_url = first_url
        res = []
        for i in itertools.count():
            api_json = self._download_webpage(next_url, playlist_id,
                note=u'Downloading song information %s/%s' % (str(i+1), track_count),
                errnote=u'Failed to download song information')
            api_data = json.loads(api_json)
            track_data = api_data[u'set']['track']
            info = {
                'id': track_data['id'],
                'url': track_data['track_file_stream_url'],
                'title': track_data['performer'] + u' - ' + track_data['name'],
                'raw_title': track_data['name'],
                'uploader_id': data['user']['login'],
                'ext': 'm4a',
            }
            res.append(info)
            if api_data['set']['at_last_track']:
                break
            next_url = 'http://8tracks.com/sets/%s/next?player=sm&mix_id=%s&format=jsonh&track_id=%s' % (session, mix_id, track_data['id'])
        return res
