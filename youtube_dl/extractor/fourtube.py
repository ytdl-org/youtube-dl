import re

from .common import InfoExtractor
from ..utils import compat_urllib_request

class FourTubeIE(InfoExtractor):
    IE_NAME = '4tube'
    _VALID_URL = r'(?:https?://)?www\.4tube\.com/videos/(?P<id>\d+)/.*'

    _TEST = {
            'url': 'http://www.4tube.com/videos/209733/hot-babe-holly-michaels-gets-her-ass-stuffed-by-black',
            'md5': '6516c8ac63b03de06bc8eac14362db4f',
            'info_dict': {
                'id': '209733',
                'ext': 'mp4',
                'title': 'Hot Babe Holly Michaels gets her ass stuffed by black'
                }
            }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage_url = 'http://www.4tube.com/videos/' + video_id
        webpage = self._download_webpage(webpage_url, video_id)

        self.report_extraction(video_id)

        playlist_json = self._html_search_regex(r'var playerConfigPlaylist\s+=\s+([^;]+)', webpage, u'Playlist')
        media_id = self._search_regex(r'idMedia:\s*(\d+)', playlist_json, u"Media Id")
        thumbnail_url = self._search_regex(r'image:\s*"([^"]*)', playlist_json, u'Thumbnail')
        sources = self._search_regex(r'sources:\s*\[([^\]]*)\]', playlist_json, u'Sources').split(',')
        title = self._search_regex(r'title:\s*"([^"]*)', playlist_json, u'Title')

        token_url = "http://tkn.4tube.com/{0}/desktop/{1}".format(media_id, "+".join(sources))
        headers = {
                b'Content-Type': b'application/x-www-form-urlencoded',
                b'Origin': b'http://www.4tube.com',
                }
        token_req = compat_urllib_request.Request(token_url, b'{}', headers)
        tokens = self._download_json(token_req, video_id)

        formats = [{
            'url': tokens[format]['token'],
            'format_id': format + 'p',
            'resolution': format + 'p',
            'quality': int(format),
            } for format in sources]

        return [{
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail_url,
            'age_limit': 18,
            'webpage_url': webpage_url,
            }]
