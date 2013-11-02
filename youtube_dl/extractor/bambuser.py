import re
import json

from .common import InfoExtractor


class BambuserIE(InfoExtractor):
    _VALID_URL = r'https?://bambuser\.com/v/(?P<id>\d+)'
    _API_KEY = '005f64509e19a868399060af746a00aa'

    _TEST = {
        u'url': u'http://bambuser.com/v/4050584',
        u'md5': u'fba8f7693e48fd4e8641b3fd5539a641',
        u'info_dict': {
            u'id': u'4050584',
            u'ext': u'flv',
            u'title': u'Education engineering days - lightning talks',
            u'duration': 3741,
            u'uploader': u'pixelversity',
            u'uploader_id': u'344706',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        info_url = ('http://player-c.api.bambuser.com/getVideo.json?'
            '&api_key=%s&vid=%s' % (self._API_KEY, video_id))
        info_json = self._download_webpage(info_url, video_id)
        info = json.loads(info_json)['result']

        return {
            'id': video_id,
            'title': info['title'],
            'url': info['url'],
            'thumbnail': info['preview'],
            'duration': int(info['length']),
            'view_count': int(info['views_total']),
            'uploader': info['username'],
            'uploader_id': info['uid'],
        }

