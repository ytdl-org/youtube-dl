# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..compat import (
    compat_urllib_parse_urlencode
)

from ..utils import (
    urlencode_postdata,
    sanitized_Request
)


class DeckoVideoIE(InfoExtractor):
    _VALID_URL = r'https?://decko.ceskatelevize.cz/video/(?P<id>.+)'
    _TEST = {
        'url': 'http://decko.ceskatelevize.cz/video/213543116070004',
#        'only_matching': True,
        'md5': '5a9752d8b1616a59a3c495af0fa344d9',
        'params': {
            'format': 'bestvideo+bestaudio/best',
            'skip_download': True
        },
        'info_dict': {
            'id': '61924494877085121-pc',
            'ext': 'mp4'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        data = {
            'playlist[0][type]': 'episode',
            'playlist[0][id]': video_id,
            'requestUrl': '',
            'requestSource': 'decko',
        }

        req = sanitized_Request(
            'http://www.ceskatelevize.cz/ivysilani/ajax/get-client-playlist',
            data=urlencode_postdata(data))

        req.add_header('Content-type', 'application/x-www-form-urlencoded')
        req.add_header('x-addr', '127.0.0.1')
        req.add_header('X-Requested-With', 'XMLHttpRequest')

        playlist1 = self._download_json(req, video_id)
        playlist2 = self._download_json(playlist1.get("url"), video_id)
        url = playlist2.get('playlist', {})[0].get('streamUrls', {}).get('main')
        return self.url_result(url)


class DeckoPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://decko.ceskatelevize.cz/(?P<id>[a-z-]+)$'
    _TEST = {
        'url': 'http://decko.ceskatelevize.cz/nejmensi-slon-na-svete',
        'playlist_count': 13
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        idec = self._html_search_regex(r'var\s+IDEC\s+=\s+\'(.+?)\'', webpage, 'IDEC')

        args = compat_urllib_parse_urlencode({"IDEC":idec})
        url = "http://decko.ceskatelevize.cz/rest/Programme/relatedVideosForEpisode?" + args
        json = self._download_json(url, video_id)
        episodes = json.get("episodes", [])

        entries = []
        for episode in episodes:
            idec = episode.get("episode", {}).get("IDEC")
            idec = idec.replace(" ", "").replace("/", "")
            url = "http://decko.ceskatelevize.cz/video/" + idec
            entries.append(self.url_result(url))

        return {
            '_type': 'playlist',
            'entries': entries
        }
