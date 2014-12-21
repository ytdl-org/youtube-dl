from __future__ import unicode_literals

import json
import time

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
)


class HypemIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?hypem\.com/track/(?P<id>[^/]+)/'
    _TEST = {
        'url': 'http://hypem.com/track/1v6ga/BODYWORK+-+TAME',
        'md5': 'b9cc91b5af8995e9f0c1cee04c575828',
        'info_dict': {
            'id': '1v6ga',
            'ext': 'mp3',
            'title': 'Tame',
            'uploader': 'BODYWORK',
        }
    }

    def _real_extract(self, url):
        track_id = self._match_id(url)

        data = {'ax': 1, 'ts': time.time()}
        data_encoded = compat_urllib_parse.urlencode(data)
        complete_url = url + "?" + data_encoded
        request = compat_urllib_request.Request(complete_url)
        response, urlh = self._download_webpage_handle(
            request, track_id, 'Downloading webpage with the url')
        cookie = urlh.headers.get('Set-Cookie', '')

        html_tracks = self._html_search_regex(
            r'(?ms)<script type="application/json" id="displayList-data">\s*(.*?)\s*</script>',
            response, 'tracks')
        try:
            track_list = json.loads(html_tracks)
            track = track_list['tracks'][0]
        except ValueError:
            raise ExtractorError('Hypemachine contained invalid JSON.')

        key = track['key']
        track_id = track['id']
        artist = track['artist']
        title = track['song']

        serve_url = "http://hypem.com/serve/source/%s/%s" % (track_id, key)
        request = compat_urllib_request.Request(
            serve_url, '', {'Content-Type': 'application/json'})
        request.add_header('cookie', cookie)
        song_data = self._download_json(request, track_id, 'Downloading metadata')
        final_url = song_data["url"]

        return {
            'id': track_id,
            'url': final_url,
            'ext': 'mp3',
            'title': title,
            'uploader': artist,
        }
