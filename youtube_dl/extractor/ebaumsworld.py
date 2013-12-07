import re

from .common import InfoExtractor
from ..utils import determine_ext


class EbaumsWorldIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ebaumsworld\.com/video/watch/(?P<id>\d+)'

    _TEST = {
        u'url': u'http://www.ebaumsworld.com/video/watch/83367677/',
        u'file': u'83367677.mp4',
        u'info_dict': {
            u'title': u'A Giant Python Opens The Door',
            u'description': u'This is how nightmares start...',
            u'uploader': u'jihadpizza',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        config = self._download_xml(
            'http://www.ebaumsworld.com/video/player/%s' % video_id, video_id)
        video_url = config.find('file').text

        return {
            'id': video_id,
            'title': config.find('title').text,
            'url': video_url,
            'ext': determine_ext(video_url),
            'description': config.find('description').text,
            'thumbnail': config.find('image').text,
            'uploader': config.find('username').text,
        }
