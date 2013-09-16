import json
import re
import socket

from .common import InfoExtractor
from ..utils import (
    compat_http_client,
    compat_urllib_error,
    compat_urllib_request,
    unified_strdate,
)


class MixcloudIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?mixcloud\.com/([\w\d-]+)/([\w\d-]+)'
    IE_NAME = u'mixcloud'

    _TEST = {
        u'url': u'http://www.mixcloud.com/dholbach/cryptkeeper/',
        u'file': u'dholbach-cryptkeeper.mp3',
        u'info_dict': {
            u'title': u'Cryptkeeper',
            u'description': u'After quite a long silence from myself, finally another Drum\'n\'Bass mix with my favourite current dance floor bangers.',
            u'uploader': u'Daniel Holbach',
            u'uploader_id': u'dholbach',
            u'upload_date': u'20111115',
        },
    }

    def check_urls(self, url_list):
        """Returns 1st active url from list"""
        for url in url_list:
            try:
                compat_urllib_request.urlopen(url)
                return url
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error):
                url = None

        return None

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        uploader = mobj.group(1)
        cloudcast_name = mobj.group(2)
        track_id = '-'.join((uploader, cloudcast_name))
        api_url = 'http://api.mixcloud.com/%s/%s/' % (uploader, cloudcast_name)
        webpage = self._download_webpage(url, track_id)
        json_data = self._download_webpage(api_url, track_id,
            u'Downloading cloudcast info')
        info = json.loads(json_data)

        preview_url = self._search_regex(r'data-preview-url="(.+?)"', webpage, u'preview url')
        song_url = preview_url.replace('/previews/', '/cloudcasts/originals/')
        template_url = re.sub(r'(stream\d*)', 'stream%d', song_url)
        final_song_url = self.check_urls(template_url % i for i in range(30))

        return {
            'id': track_id,
            'title': info['name'],
            'url': final_song_url,
            'ext': 'mp3',
            'description': info['description'],
            'thumbnail': info['pictures'].get('extra_large'),
            'uploader': info['user']['name'],
            'uploader_id': info['user']['username'],
            'upload_date': unified_strdate(info['created_time']),
            'view_count': info['play_count'],
        }
