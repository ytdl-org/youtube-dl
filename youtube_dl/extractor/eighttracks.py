import json
import random
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class EightTracksIE(InfoExtractor):
    IE_NAME = '8tracks'
    _VALID_URL = r'https?://8tracks\.com/(?P<user>[^/]+)/(?P<id>[^/#]+)(?:#.*)?$'
    _TEST = {
        u"name": u"EightTracks",
        u"url": u"http://8tracks.com/ytdl/youtube-dl-test-tracks-a",
        u"playlist": [
            {
                u"file": u"11885610.m4a",
                u"md5": u"96ce57f24389fc8734ce47f4c1abcc55",
                u"info_dict": {
                    u"title": u"youtue-dl project<>\"' - youtube-dl test track 1 \"'/\\\u00e4\u21ad",
                    u"uploader_id": u"ytdl"
                }
            },
            {
                u"file": u"11885608.m4a",
                u"md5": u"4ab26f05c1f7291ea460a3920be8021f",
                u"info_dict": {
                    u"title": u"youtube-dl project - youtube-dl test track 2 \"'/\\\u00e4\u21ad",
                    u"uploader_id": u"ytdl"
                }
            },
            {
                u"file": u"11885679.m4a",
                u"md5": u"d30b5b5f74217410f4689605c35d1fd7",
                u"info_dict": {
                    u"title": u"youtube-dl project as well - youtube-dl test track 3 \"'/\\\u00e4\u21ad",
                    u"uploader_id": u"ytdl"
                }
            },
            {
                u"file": u"11885680.m4a",
                u"md5": u"4eb0a669317cd725f6bbd336a29f923a",
                u"info_dict": {
                    u"title": u"youtube-dl project as well - youtube-dl test track 4 \"'/\\\u00e4\u21ad",
                    u"uploader_id": u"ytdl"
                }
            },
            {
                u"file": u"11885682.m4a",
                u"md5": u"1893e872e263a2705558d1d319ad19e8",
                u"info_dict": {
                    u"title": u"PH - youtube-dl test track 5 \"'/\\\u00e4\u21ad",
                    u"uploader_id": u"ytdl"
                }
            },
            {
                u"file": u"11885683.m4a",
                u"md5": u"b673c46f47a216ab1741ae8836af5899",
                u"info_dict": {
                    u"title": u"PH - youtube-dl test track 6 \"'/\\\u00e4\u21ad",
                    u"uploader_id": u"ytdl"
                }
            },
            {
                u"file": u"11885684.m4a",
                u"md5": u"1d74534e95df54986da7f5abf7d842b7",
                u"info_dict": {
                    u"title": u"phihag - youtube-dl test track 7 \"'/\\\u00e4\u21ad",
                    u"uploader_id": u"ytdl"
                }
            },
            {
                u"file": u"11885685.m4a",
                u"md5": u"f081f47af8f6ae782ed131d38b9cd1c0",
                u"info_dict": {
                    u"title": u"phihag - youtube-dl test track 8 \"'/\\\u00e4\u21ad",
                    u"uploader_id": u"ytdl"
                }
            }
        ]
    }


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
        for i in range(track_count):
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
            next_url = 'http://8tracks.com/sets/%s/next?player=sm&mix_id=%s&format=jsonh&track_id=%s' % (session, mix_id, track_data['id'])
        return res
