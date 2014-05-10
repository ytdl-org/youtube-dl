#! -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import hashlib

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_request,
    compat_urlparse,
)

class FC2IE(InfoExtractor):
    _VALID_URL = r'^(?:http://)?video\.fc2\.com/(?P<lang>[^/]+)/content/(?P<id>[^/]+)'
    IE_NAME = u'fc2'
    _TEST = {
        u'url': u'http://video.fc2.com/en/content/20121103kUan1KHs',
        u'file': u'20121103kUan1KHs.flv',
        u'md5': u'a6ebe8ebe0396518689d963774a54eb7',
        u'info_dict': {
            u'title': u'Boxing again with Puff',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        self._downloader.cookiejar.clear_session_cookies()  # must clear

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        refer = url.replace('/content/', '/a/content/')

        m = hashlib.md5()
        m.update(video_id+'_gGddgPfeaf_gzyr')
        mimi = m.hexdigest()

        info_url = "http://video.fc2.com/ginfo.php?mimi={1:s}&href={2:s}&v={0:s}&fversion=WIN%2011%2C6%2C602%2C180&from=2&otag=0&upid={0:s}&tk=null&".format(video_id, mimi, compat_urllib_request.quote(refer, safe='').replace('.','%2E'))

        info_webpage = self._download_webpage(
            info_url, video_id, note=u'Downloading info page')

        info = compat_urlparse.parse_qs(info_webpage)

        if 'err_code' in info:
            raise ExtractorError(u'Error code: %s' % info['err_code'][0])

        video_url = info['filepath'][0]+'?mid='+info['mid'][0]

        return {
            'id': video_id,
            'title': info['title'][0],
            'url': video_url,
            'ext': 'flv',
            'thumbnail': thumbnail,
        }
