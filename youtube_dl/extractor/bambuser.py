import re
import json
import itertools

from .common import InfoExtractor
from ..utils import (
    compat_urllib_request,
)


class BambuserIE(InfoExtractor):
    IE_NAME = u'bambuser'
    _VALID_URL = r'https?://bambuser\.com/v/(?P<id>\d+)'
    _API_KEY = '005f64509e19a868399060af746a00aa'

    _TEST = {
        u'url': u'http://bambuser.com/v/4050584',
        # MD5 seems to be flaky, see https://travis-ci.org/rg3/youtube-dl/jobs/14051016#L388
        #u'md5': u'fba8f7693e48fd4e8641b3fd5539a641',
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
            'thumbnail': info.get('preview'),
            'duration': int(info['length']),
            'view_count': int(info['views_total']),
            'uploader': info['username'],
            'uploader_id': info['uid'],
        }


class BambuserChannelIE(InfoExtractor):
    IE_NAME = u'bambuser:channel'
    _VALID_URL = r'http://bambuser.com/channel/(?P<user>.*?)(?:/|#|\?|$)'
    # The maximum number we can get with each request
    _STEP = 50

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user = mobj.group('user')
        urls = []
        last_id = ''
        for i in itertools.count(1):
            req_url = ('http://bambuser.com/xhr-api/index.php?username={user}'
                '&sort=created&access_mode=0%2C1%2C2&limit={count}'
                '&method=broadcast&format=json&vid_older_than={last}'
                ).format(user=user, count=self._STEP, last=last_id)
            req = compat_urllib_request.Request(req_url)
            # Without setting this header, we wouldn't get any result
            req.add_header('Referer', 'http://bambuser.com/channel/%s' % user)
            info_json = self._download_webpage(req, user,
                u'Downloading page %d' % i)
            results = json.loads(info_json)['result']
            if len(results) == 0:
                break
            last_id = results[-1]['vid']
            urls.extend(self.url_result(v['page'], 'Bambuser') for v in results)

        return {
            '_type': 'playlist',
            'title': user,
            'entries': urls,
        }
