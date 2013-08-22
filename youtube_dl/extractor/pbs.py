import re
import json

from .common import InfoExtractor


class PBSIE(InfoExtractor):
    _VALID_URL = r'https?://video.pbs.org/video/(?P<id>\d+)/?'

    _TEST = {
        u'url': u'http://video.pbs.org/video/2365006249/',
        u'file': u'2365006249.mp4',
        u'md5': 'ce1888486f0908d555a8093cac9a7362',
        u'info_dict': {
            u'title': u'A More Perfect Union',
            u'description': u'md5:ba0c207295339c8d6eced00b7c363c6a',
            u'duration': 3190,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        info_url = 'http://video.pbs.org/videoInfo/%s?format=json' % video_id
        info_page = self._download_webpage(info_url, video_id)
        info =json.loads(info_page)
        return {'id': video_id,
                'title': info['title'],
                'url': info['alternate_encoding']['url'],
                'ext': 'mp4',
                'description': info['program'].get('description'),
                'thumbnail': info.get('image_url'),
                'duration': info.get('duration'),
                }
