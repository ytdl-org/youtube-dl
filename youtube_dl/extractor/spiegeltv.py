# coding: utf-8
from __future__ import unicode_literals

import re
import json
import urllib
from .common import InfoExtractor

class SpiegeltvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?spiegel\.tv/filme/(?P<id>[\-a-z0-9]+)'
    _TEST = {
        'url': 'http://www.spiegel.tv/filme/flug-mh370/',
				'md5': '700d62dc485f3a81cf9d52144e5ead59',
        'info_dict': {
            'id': 'flug-mh370',
            'ext': 'm4v',
            'title': 'Flug MH370',
            'description': 'Das Rätsel um die Boeing 777 der Malaysia-Airlines',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        # TODO more code goes here, for example ...
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h1.*?>(.*?)</h1>', webpage, 'title')

        apihost           = 'http://spiegeltv-ivms2-restapi.s3.amazonaws.com';

        version_json_code = urllib.urlopen('%s/version.json' % apihost).read()
        version_json      = json.loads(version_json_code)
        version_name      = version_json['version_name']

        slug_json_code    = urllib.urlopen('%s/%s/restapi/slugs/%s.json' % (apihost, version_name, video_id)).read()
        slug_json         = json.loads(slug_json_code)
        oid               = slug_json['object_id']
              
        media_json_code   = urllib.urlopen('%s/%s/restapi/media/%s.json' % (apihost, version_name, oid)).read()
        media_json        = json.loads(media_json_code)

        uuid              = media_json['uuid']
        is_wide           = media_json['is_wide']

        server_json_code  = urllib.urlopen('http://www.spiegel.tv/streaming_servers/').read()
        server_json       = json.loads(server_json_code)
        server            = server_json[0]['endpoint']

        thumbnails = []
        for image in media_json['images']:
          thumbnails.append({'url': image['url'], 'resolution': str(image['width']) + 'x' + str(image['height']) })

        description = media_json['subtitle']
        duration = int(round(media_json['duration_in_ms'] / 1000))

        if is_wide:
          format = '16x9'
        else:
          format = '4x3'

        url = server + 'mp4:' + uuid + '_spiegeltv_0500_' + format + '.m4v'

        return_dict = {
            'id': video_id,
            'title': title,
            'url': url,
            'ext': 'm4v',
            'description': description,
            'duration': duration,
            'thumbnails': thumbnails
        }
        return return_dict
