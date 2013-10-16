# encoding: utf-8
import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    compat_str,
    ExtractorError,
)


class RutubeIE(InfoExtractor):
    _VALID_URL = r'https?://rutube.ru/video/(?P<long_id>\w+)'

    _TEST = {
        u'url': u'http://rutube.ru/video/3eac3b4561676c17df9132a9a1e62e3e/',
        u'file': u'3eac3b4561676c17df9132a9a1e62e3e.mp4',
        u'info_dict': {
            u'title': u'Раненный кенгуру забежал в аптеку',
            u'uploader': u'NTDRussian',
            u'uploader_id': u'29790',
        },
        u'params': {
            # It requires ffmpeg (m3u8 download)
            u'skip_download': True,
        },
    }

    def _get_api_response(self, short_id, subpath):
        api_url = 'http://rutube.ru/api/play/%s/%s/?format=json' % (subpath, short_id)
        response_json = self._download_webpage(api_url, short_id,
            u'Downloading %s json' % subpath)
        return json.loads(response_json)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        long_id = mobj.group('long_id')
        webpage = self._download_webpage(url, long_id)
        og_video = self._og_search_video_url(webpage)
        short_id = compat_urlparse.urlparse(og_video).path[1:]
        options = self._get_api_response(short_id, 'options')
        trackinfo = self._get_api_response(short_id, 'trackinfo')
        # Some videos don't have the author field
        author = trackinfo.get('author') or {}
        m3u8_url = trackinfo['video_balancer'].get('m3u8')
        if m3u8_url is None:
            raise ExtractorError(u'Couldn\'t find m3u8 manifest url')

        return {
            'id': trackinfo['id'],
            'title': trackinfo['title'],
            'url': m3u8_url,
            'ext': 'mp4',
            'thumbnail': options['thumbnail_url'],
            'uploader': author.get('name'),
            'uploader_id': compat_str(author['id']) if author else None,
        }
